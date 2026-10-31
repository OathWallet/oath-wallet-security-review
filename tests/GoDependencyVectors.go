// Public known-answer data from RFC 7914 sections 11 and 12:
// https://www.rfc-editor.org/rfc/rfc7914.html#section-11
// No wallet keys or real passwords. Imports use the reviewed bridge's go.mod.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/kkdai/bstream"
	"golang.org/x/crypto/pbkdf2"
	"golang.org/x/crypto/scrypt"
)

func require(ok bool, label string) {
	if !ok {
		panic(label)
	}
}
func equalHex(actual []byte, expected string) bool {
	want, err := hex.DecodeString(expected)
	require(err == nil, "invalid test vector")
	return bytes.Equal(actual, want)
}
func main() {
	start := time.Now()
	for i, v := range []struct {
		p, s       string
		iterations int
		want       string
	}{
		{"passwd", "salt", 1, "55ac046e56e3089fec1691c22544b605f94185216dde0465e68b9d57c20dacbc49ca9cccf179b645991664b39d77ef317c71b845b1e30bd509112041d3a19783"},
		{"Password", "NaCl", 80000, "4ddcd8f60b98be21830cee5ef22701f9641a4418d04c0414aeff08876b34ab56a1d425a1225833549adb841b51c9b3176a272bdebba1d078478f62b397f33c8d"},
	} {
		require(equalHex(pbkdf2.Key([]byte(v.p), []byte(v.s), v.iterations, 64, sha256.New), v.want), fmt.Sprint("RFC PBKDF2 vector ", i))
	}
	for i, v := range []struct {
		p, s           string
		n, r, parallel int
		want           string
	}{
		{"", "", 16, 1, 1, "77d6576238657b203b19ca42c18a0497f16b4844e3074ae8dfdffa3fede21442fcd0069ded0948f8326a753a0fc81f17e8d3e0fb2e0d3628cf35e20c38d18906"},
		{"password", "NaCl", 1024, 8, 16, "fdbabe1c9d3472007856e7190d01e9fe7c6ad7cbc8237830e77376634b3731622eaf30d92e22a3886ff109279d9830dac727afb94a83ee6d8360cbdfa2cc0640"},
		{"pleaseletmein", "SodiumChloride", 16384, 8, 1, "7023bdcb3afd7348461c06cd81fd38ebfda8fbba904f8e3ea9b543f6545da1f2d5432955613f0fcf62d49705242a9af9e61e85dc0d651e40dfcf017b45575887"},
	} {
		got, err := scrypt.Key([]byte(v.p), []byte(v.s), v.n, v.r, v.parallel, 64)
		require(err == nil && equalHex(got, v.want), fmt.Sprint("RFC scrypt vector ", i))
	}
	// Bounded, deterministic fuzzing of the exact 24 x 11-bit aezeed path.
	// Expected values use direct byte operations, independent of BStream.
	seed := uint64(0x4f41544820261031)
	next := func() byte { seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17; return byte(seed) }
	for n := 0; n < 1000; n++ {
		data := make([]byte, 33)
		for i := range data {
			data[i] = next()
		}
		reader, writer := bstream.NewBStreamReader(data), bstream.NewBStreamWriter(33)
		for word := 0; word < 24; word++ {
			var expected uint64
			for bit := 0; bit < 11; bit++ {
				pos := word*11 + bit
				expected = expected<<1 | uint64((data[pos/8]>>(7-pos%8))&1)
			}
			got, err := reader.ReadBits(11)
			require(err == nil && got == expected, "bitstream read differs from byte reference")
			writer.WriteBits(expected, 11)
		}
		require(bytes.Equal(writer.Bytes(), data), "bitstream write differs from original bytes")
		_, err := reader.ReadBit()
		require(err == io.EOF, "bitstream must stop at 264 bits")
	}
	result := map[string]any{"status": "passed", "known_answer_vectors": 5, "bitstream_cases": 1000,
		"seed": "0x4f41544820261031", "duration_seconds": time.Since(start).Seconds(),
		"excluded": "RFC scrypt 1GiB vector; cryptographic side-channel analysis; archive equivalence"}
	require(json.NewEncoder(os.Stdout).Encode(result) == nil, "write result")
}
