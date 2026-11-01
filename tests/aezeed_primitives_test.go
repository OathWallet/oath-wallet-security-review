package primitiveaudit

import (
	"bytes"
	"crypto/aes"
	"encoding/hex"
	"testing"

	"gitlab.com/yawning/bsaes.git/ct32"
	"gitlab.com/yawning/bsaes.git/ct64"
)

// Independent byte-field arithmetic; the production implementation uses a
// bitsliced Boolean circuit, not this inversion/affine construction.
func multiply(a, b byte) byte {
	var result byte
	for b != 0 {
		if b&1 != 0 {
			result ^= a
		}
		high := a&128 != 0
		a <<= 1
		if high {
			a ^= 0x1b
		}
		b >>= 1
	}
	return result
}

func substitute(x byte) byte {
	var inverse byte
	if x != 0 {
		inverse = 1
		for n := 0; n < 254; n++ {
			inverse = multiply(inverse, x)
		}
	}
	result := inverse ^ 0x63
	for shift := uint(1); shift <= 4; shift++ {
		result ^= inverse<<shift | inverse>>(8-shift)
	}
	return result
}

func TestEverySBoxInputInEveryLane(t *testing.T) {
	for offset := 0; offset < 256; offset++ {
		var q [8]uint64
		for lane := 0; lane < 64; lane++ {
			value := byte(offset + lane)
			for bit := 0; bit < 8; bit++ {
				q[bit] |= uint64((value>>bit)&1) << lane
			}
		}
		original := q
		ct64.Sbox(&q)
		for lane := 0; lane < 64; lane++ {
			var actual byte
			for bit := 0; bit < 8; bit++ {
				actual |= byte((q[bit]>>lane)&1) << bit
			}
			if actual != substitute(byte(offset+lane)) {
				t.Fatalf("S-box mismatch at offset %d lane %d", offset, lane)
			}
		}
		ct64.InvSbox(&q)
		if q != original {
			t.Fatal("inverse S-box mismatch")
		}
	}
}

func TestKnownAnswerAndDeterministicDifferential(t *testing.T) {
	// Public FIPS-197 AES-128 example, never an application wallet key.
	key, _ := hex.DecodeString("000102030405060708090a0b0c0d0e0f")
	plain, _ := hex.DecodeString("00112233445566778899aabbccddeeff")
	want, _ := hex.DecodeString("69c4e0d86a7b0430d8cdb78070b4c55a")
	actual := make([]byte, 16)
	ct64.NewCipher(key).Encrypt(actual, plain)
	if !bytes.Equal(actual, want) {
		t.Fatal("FIPS-197 known-answer mismatch")
	}
	state := uint64(0x4f41544841455331)
	fill := func(b []byte) {
		for i := range b {
			state ^= state << 13
			state ^= state >> 7
			state ^= state << 17
			b[i] = byte(state)
		}
	}
	for _, size := range []int{16, 24, 32} {
		for sample := 0; sample < 256; sample++ {
			key := make([]byte, size)
			fill(key)
			plain := make([]byte, 64)
			fill(plain)
			candidate := ct64.NewCipher(key)
			reference, err := aes.NewCipher(key)
			if err != nil {
				t.Fatal(err)
			}
			want, actual := make([]byte, 64), make([]byte, 64)
			for offset := 0; offset < 64; offset += 16 {
				reference.Encrypt(want[offset:], plain[offset:])
				candidate.Encrypt(actual[offset:], plain[offset:])
			}
			if !bytes.Equal(actual, want) {
				t.Fatal("AES differential mismatch")
			}
			bulk := candidate.(interface {
				BulkEncrypt([]byte, []byte)
				BulkDecrypt([]byte, []byte)
			})
			bulk.BulkEncrypt(actual, plain)
			if !bytes.Equal(actual, want) {
				t.Fatal("four-block differential mismatch")
			}
			bulk.BulkDecrypt(actual, actual)
			if !bytes.Equal(actual, plain) {
				t.Fatal("four-block in-place decryption mismatch")
			}
			for offset := 0; offset < 64; offset += 16 {
				candidate.Decrypt(want[offset:], want[offset:])
			}
			if !bytes.Equal(want, plain) {
				t.Fatal("single-block in-place decryption mismatch")
			}
		}
	}
}

func TestResetAndShortBuffersReject(t *testing.T) {
	expectPanic := func(run func()) {
		t.Helper()
		defer func() {
			if recover() == nil {
				t.Error("operation did not reject invalid state")
			}
		}()
		run()
	}
	block := ct64.NewCipher(make([]byte, 16))
	for n := 0; n < 16; n++ {
		expectPanic(func() { block.Encrypt(make([]byte, 16), make([]byte, n)) })
		expectPanic(func() { block.Decrypt(make([]byte, n), make([]byte, 16)) })
	}
	reset := block.(interface{ Reset() })
	reset.Reset()
	reset.Reset()
	expectPanic(func() { block.Encrypt(make([]byte, 16), make([]byte, 16)) })
	expectPanic(func() { block.Decrypt(make([]byte, 16), make([]byte, 16)) })
}

func TestCT32EverySBoxInputInEveryLane(t *testing.T) {
	for offset := 0; offset < 256; offset++ {
		var q [8]uint32
		for lane := 0; lane < 32; lane++ {
			value := byte(offset + lane)
			for bit := 0; bit < 8; bit++ {
				q[bit] |= uint32((value>>bit)&1) << lane
			}
		}
		original := q
		ct32.Sbox(&q)
		for lane := 0; lane < 32; lane++ {
			var actual byte
			for bit := 0; bit < 8; bit++ {
				actual |= byte((q[bit]>>lane)&1) << bit
			}
			if actual != substitute(byte(offset+lane)) {
				t.Fatalf("S-box mismatch at offset %d lane %d", offset, lane)
			}
		}
		ct32.InvSbox(&q)
		if q != original {
			t.Fatal("inverse S-box mismatch")
		}
	}
}

func TestCT32KnownAnswerAndDeterministicDifferential(t *testing.T) {
	// Public FIPS-197 AES-128 example, never an application wallet key.
	key, _ := hex.DecodeString("000102030405060708090a0b0c0d0e0f")
	plain, _ := hex.DecodeString("00112233445566778899aabbccddeeff")
	want, _ := hex.DecodeString("69c4e0d86a7b0430d8cdb78070b4c55a")
	actual := make([]byte, 16)
	ct32.NewCipher(key).Encrypt(actual, plain)
	if !bytes.Equal(actual, want) {
		t.Fatal("FIPS-197 known-answer mismatch")
	}
	state := uint64(0x4f41544841455331)
	fill := func(b []byte) {
		for i := range b {
			state ^= state << 13
			state ^= state >> 7
			state ^= state << 17
			b[i] = byte(state)
		}
	}
	for _, size := range []int{16, 24, 32} {
		for sample := 0; sample < 256; sample++ {
			key := make([]byte, size)
			fill(key)
			plain := make([]byte, 32)
			fill(plain)
			candidate := ct32.NewCipher(key)
			reference, err := aes.NewCipher(key)
			if err != nil {
				t.Fatal(err)
			}
			want, actual := make([]byte, 32), make([]byte, 32)
			for offset := 0; offset < 32; offset += 16 {
				reference.Encrypt(want[offset:], plain[offset:])
				candidate.Encrypt(actual[offset:], plain[offset:])
			}
			if !bytes.Equal(actual, want) {
				t.Fatal("AES differential mismatch")
			}
			bulk := candidate.(interface {
				BulkEncrypt([]byte, []byte)
				BulkDecrypt([]byte, []byte)
			})
			bulk.BulkEncrypt(actual, plain)
			if !bytes.Equal(actual, want) {
				t.Fatal("two-block differential mismatch")
			}
			bulk.BulkDecrypt(actual, actual)
			if !bytes.Equal(actual, plain) {
				t.Fatal("two-block in-place decryption mismatch")
			}
			for offset := 0; offset < 32; offset += 16 {
				candidate.Decrypt(want[offset:], want[offset:])
			}
			if !bytes.Equal(want, plain) {
				t.Fatal("single-block in-place decryption mismatch")
			}
		}
	}
}

func TestCT32ResetAndShortBuffersReject(t *testing.T) {
	expectPanic := func(run func()) {
		t.Helper()
		defer func() {
			if recover() == nil {
				t.Error("operation did not reject invalid state")
			}
		}()
		run()
	}
	block := ct32.NewCipher(make([]byte, 16))
	for n := 0; n < 16; n++ {
		expectPanic(func() { block.Encrypt(make([]byte, 16), make([]byte, n)) })
		expectPanic(func() { block.Decrypt(make([]byte, n), make([]byte, 16)) })
	}
	reset := block.(interface{ Reset() })
	reset.Reset()
	reset.Reset()
	expectPanic(func() { block.Encrypt(make([]byte, 16), make([]byte, 16)) })
	expectPanic(func() { block.Decrypt(make([]byte, 16), make([]byte, 16)) })
}
