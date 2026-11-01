package primitiveaudit

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"encoding"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"

	"github.com/Yawning/aez"
	"gitlab.com/yawning/bsaes.git/ct32"
	"gitlab.com/yawning/bsaes.git/ct64"
	"gitlab.com/yawning/bsaes.git/ghash"
	"golang.org/x/crypto/blake2b"
)

// Bit-serial GF(2^128) reference using the GCM polynomial, independent of
// production's masked 64-bit multiplication and bit-reversal implementation.
func referenceGHASH(y, h [16]byte, data []byte) [16]byte {
	for len(data) > 0 {
		n := len(data)
		if n > 16 {
			n = 16
		}
		for i := 0; i < n; i++ {
			y[i] ^= data[i]
		}
		data = data[n:]
		var z [16]byte
		v := h
		for bit := 0; bit < 128; bit++ {
			if y[bit/8]&(1<<uint(7-bit%8)) != 0 {
				for i := range z {
					z[i] ^= v[i]
				}
			}
			low := v[15] & 1
			for i := 15; i > 0; i-- {
				v[i] = v[i]>>1 | v[i-1]<<7
			}
			v[0] >>= 1
			if low != 0 {
				v[0] ^= 0xe1
			}
		}
		y = z
	}
	return y
}

func TestGHASHIndependentPolynomial(t *testing.T) {
	for n := 0; n <= 513; n++ {
		var h, y [16]byte
		for i := range h {
			h[i] = byte(n + 17*i)
			y[i] = byte(n*3 + i)
		}
		data := make([]byte, n)
		for i := range data {
			data[i] = byte(i*37 + n)
		}
		want := referenceGHASH(y, h, data)
		actual := y
		ghash.Ghash(&actual, &h, data)
		if actual != want {
			t.Fatalf("GHASH mismatch length %d", n)
		}
	}
}

func TestBlakeIndependentVectors(t *testing.T) {
	raw, err := os.ReadFile("blake-vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors []struct {
		Size                 int
		Key, Message, Digest string
	}
	if err = json.Unmarshal(raw, &vectors); err != nil {
		t.Fatal(err)
	}
	if len(vectors) != 220 {
		t.Fatal("missing vectors")
	}
	for _, v := range vectors {
		key, e := hex.DecodeString(v.Key)
		if e != nil {
			t.Fatal(e)
		}
		message, e := hex.DecodeString(v.Message)
		if e != nil {
			t.Fatal(e)
		}
		want, e := hex.DecodeString(v.Digest)
		if e != nil {
			t.Fatal(e)
		}
		for _, chunk := range []int{1, 17, 128, 511} {
			h, e := blake2b.New(v.Size, key)
			if e != nil {
				t.Fatal(e)
			}
			for repetition := 0; repetition < 2; repetition++ {
				for p := 0; p < len(message); p += chunk {
					end := p + chunk
					if end > len(message) {
						end = len(message)
					}
					h.Write(message[p:end])
				}
				if !bytes.Equal(h.Sum(nil), want) || !bytes.Equal(h.Sum(nil), want) {
					t.Fatalf("BLAKE2 vector size %d message %d chunk %d", v.Size, len(message), chunk)
				}
				h.Reset()
			}
		}
	}
}

func TestAEZBoundariesAndTamperRejection(t *testing.T) {
	key := bytes.Repeat([]byte{0x24}, 32)
	nonce := []byte("synthetic nonce")
	ad := [][]byte{[]byte("synthetic aad")}
	for n := 0; n <= 129; n++ {
		plain := make([]byte, n)
		for i := range plain {
			plain[i] = byte(i*29 + n)
		}
		// Oath/LND uses tau=4, nil nonce, one AD item, 19 plaintext bytes.
		// tau=16 also covers the generic authenticated-cipher API.
		for _, tau := range []int{4, 16} {
			encrypted := aez.Encrypt(key, nonce, ad, tau, plain, nil)
			decoded, ok := aez.Decrypt(key, nonce, ad, tau, encrypted, nil)
			if !ok || !bytes.Equal(decoded, plain) {
				t.Fatalf("roundtrip n=%d tau=%d", n, tau)
			}
			for i := range encrypted {
				tampered := append([]byte(nil), encrypted...)
				tampered[i] ^= 0x80
				result, ok := aez.Decrypt(key, nonce, ad, tau, tampered, nil)
				if ok || result != nil {
					t.Fatalf("tampered input accepted n=%d position=%d", n, i)
				}
			}
			wrongKey := append([]byte(nil), key...)
			wrongKey[0] ^= 1
			for variant := 0; variant < 3; variant++ {
				k, no, a := key, nonce, ad
				if variant == 0 {
					k = wrongKey
				}
				if variant == 1 {
					no = []byte("different nonce")
				}
				if variant == 2 {
					a = [][]byte{[]byte("different aad")}
				}
				result, ok := aez.Decrypt(k, no, a, tau, encrypted, nil)
				if ok || result != nil {
					t.Fatal("incorrect context accepted")
				}
			}
		}
	}
}

func TestBlockModesDifferential(t *testing.T) {
	for _, factory := range []func([]byte) cipher.Block{ct32.NewCipher, ct64.NewCipher} {
		for _, size := range []int{16, 24, 32} {
			key := bytes.Repeat([]byte{byte(size)}, size)
			standard, _ := aes.NewCipher(key)
			for _, n := range []int{0, 1, 15, 16, 17, 31, 32, 33, 63, 64, 65, 127, 128, 129, 513} {
				data := bytes.Repeat([]byte{byte(n)}, n)
				iv := bytes.Repeat([]byte{0xff}, 16)
				want, got := make([]byte, n), make([]byte, n)
				cipher.NewCTR(standard, iv).XORKeyStream(want, data)
				stream := cipher.NewCTR(factory(key), iv)
				for start := 0; start < n; {
					end := start + 7
					if end > n {
						end = n
					}
					stream.XORKeyStream(got[start:end], data[start:end])
					start = end
				}
				if !bytes.Equal(got, want) {
					t.Fatal("CTR mismatch")
				}
				if n%16 == 0 {
					cipher.NewCBCEncrypter(standard, iv).CryptBlocks(want, data)
					copy(got, want)
					cipher.NewCBCDecrypter(factory(key), iv).CryptBlocks(got, got)
					if !bytes.Equal(got, data) {
						t.Fatal("CBC mismatch")
					}
				}
				for _, nonceSize := range []int{1, 12, 16, 17} {
					// Invoke the legacy specialized mode directly; Go's current NewGCM
					// fallback interface has a different two-argument signature.
					candidate, e := factory(key).(interface {
						NewGCM(int) (cipher.AEAD, error)
					}).NewGCM(nonceSize)
					if e != nil {
						t.Fatal(e)
					}
					reference, e := cipher.NewGCMWithNonceSize(standard, nonceSize)
					if e != nil {
						t.Fatal(e)
					}
					nonce := bytes.Repeat([]byte{0x33}, nonceSize)
					ad := bytes.Repeat([]byte{0x44}, n+3)
					want := reference.Seal(nil, nonce, data, ad)
					got := candidate.Seal(nil, nonce, data, ad)
					if !bytes.Equal(got, want) {
						t.Fatal("GCM mismatch")
					}
					opened, e := candidate.Open(nil, nonce, got, ad)
					if e != nil || !bytes.Equal(opened, data) {
						t.Fatal("GCM open mismatch")
					}
					got[len(got)-1] ^= 1
					prefix := []byte("unchanged")
					opened, e = candidate.Open(prefix, nonce, got, ad)
					if e == nil || opened != nil || string(prefix) != "unchanged" {
						t.Fatal("GCM authentication failed to protect output")
					}
				}
			}
		}
	}
}

// These tests characterize defects in dependency APIs unused by Oath's bridge.
// A passing characterization means the hazard was reproduced, NOT repaired.
func TestKnownUnusedCBCPartialBlockHazard(t *testing.T) {
	block := ct64.NewCipher(make([]byte, 16))
	dst := bytes.Repeat([]byte{0x55}, 17)
	cipher.NewCBCDecrypter(block, make([]byte, 16)).CryptBlocks(dst, make([]byte, 17))
	if dst[16] != 0x55 {
		t.Fatal("expected untouched trailing byte")
	}
	standard, _ := aes.NewCipher(make([]byte, 16))
	rejected := false
	func() {
		defer func() { rejected = recover() != nil }()
		cipher.NewCBCDecrypter(standard, make([]byte, 16)).CryptBlocks(make([]byte, 17), make([]byte, 17))
	}()
	if !rejected {
		t.Fatal("reference did not reject partial block")
	}
}

func TestKnownUnusedBlakeStateHazard(t *testing.T) {
	for _, offset := range []int{3 + 8*8 + 2*8, 3 + 8*8 + 2*8 + 1 + 128} {
		h, _ := blake2b.New(48, nil)
		state, err := h.(encoding.BinaryMarshaler).MarshalBinary()
		if err != nil {
			t.Fatal(err)
		}
		state[offset] = 255
		if err = h.(encoding.BinaryUnmarshaler).UnmarshalBinary(state); err != nil {
			t.Fatal("hazard changed: malformed state now rejected")
		}
		panicked := false
		func() { defer func() { panicked = recover() != nil }(); h.Sum(nil) }()
		if !panicked {
			t.Fatal("expected malformed digest state panic")
		}
	}
}

// Bounded 512 MiB synthetic AAD exercises the actual implementation at
// its 32-bit bit-length overflow boundary. No plaintext is allocated.
func TestKnownUnusedGCMLengthHazard(t *testing.T) {
	key := make([]byte, 16)
	nonce := make([]byte, 12)
	ad := make([]byte, 1<<29)
	standard, _ := aes.NewCipher(key)
	reference, _ := cipher.NewGCM(standard)
	candidate, _ := ct64.NewCipher(key).(interface {
		NewGCM(int) (cipher.AEAD, error)
	}).NewGCM(12)
	expected := reference.Seal(nil, nonce, nil, ad)
	actual := candidate.Seal(nil, nonce, nil, ad)
	if bytes.Equal(actual, expected) {
		t.Fatal("expected documented length truncation to differ")
	}
	if _, err := reference.Open(nil, nonce, actual, ad); err == nil {
		t.Fatal("standard GCM unexpectedly accepted truncated-length tag")
	}
	t.Log("Reproduced 512 MiB AAD tag mismatch; no plaintext and no production inputs")
}
