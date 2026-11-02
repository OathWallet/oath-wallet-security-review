// Public deterministic fixtures. The two counter values were selected for overlapping format checksums.
package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/btcsuite/btcd/btcutil"
	"github.com/btcsuite/btcd/btcutil/hdkeychain"
	"github.com/btcsuite/btcd/chaincfg"
	"github.com/lightningnetwork/lnd/aezeed"
	"golang.org/x/crypto/pbkdf2"
)

func address(seed []byte, electrum bool) string {
	k, err := hdkeychain.NewMaster(seed, &chaincfg.MainNetParams)
	if err != nil {
		panic(err)
	}
	path := []uint32{84 | 1<<31, 1 << 31, 1 << 31, 0, 0}
	if electrum {
		path = []uint32{0, 0}
	}
	for _, v := range path {
		k, err = k.Derive(v)
		if err != nil {
			panic(err)
		}
	}
	point, err := k.ECPubKey()
	if err != nil {
		panic(err)
	}
	hash := btcutil.Hash160(point.SerializeCompressed())
	if electrum {
		a, err := btcutil.NewAddressPubKeyHash(hash, &chaincfg.MainNetParams)
		if err != nil {
			panic(err)
		}
		return a.EncodeAddress()
	}
	a, err := btcutil.NewAddressWitnessPubKeyHash(hash, &chaincfg.MainNetParams)
	if err != nil {
		panic(err)
	}
	return a.EncodeAddress()
}

func main() {
	i := uint32(285)
	if len(os.Args) == 2 && os.Args[1] == "all-formats" {
		i = 50579
	} else if len(os.Args) != 1 {
		panic("unknown fixture")
	}
	var entropy [16]byte
	copy(entropy[:], []byte("oath-fixture"))
	binary.BigEndian.PutUint32(entropy[12:], i)
	seed, err := aezeed.New(0, &entropy, time.Unix(1521799345, 0), aezeed.WithRandomnessSource(bytes.NewReader([]byte("salt1"))))
	if err != nil {
		panic(err)
	}
	wire, err := seed.Encipher(nil)
	if err != nil {
		panic(err)
	}
	if sha256.Sum256(wire[:32])[0] != wire[32] {
		panic("BIP39 checksum")
	}
	words, err := seed.ToMnemonic(nil)
	if err != nil {
		panic(err)
	}
	proof, err := words.ToCipherSeed(nil)
	if err != nil || proof.Entropy != entropy {
		panic("LND round trip")
	}
	phrase := strings.Join(words[:], " ")
	result := map[string]any{"iteration": i, "words": phrase, "aezeed_address": address(entropy[:], false), "bip39_address": address(pbkdf2.Key([]byte(phrase), []byte("mnemonic"), 2048, 64, sha512.New), false)}
	if i == 50579 {
		mac := hmac.New(sha512.New, []byte("Seed version"))
		mac.Write([]byte(phrase))
		if mac.Sum(nil)[0] != 1 {
			panic("Electrum version")
		}
		result["electrum_address"] = address(pbkdf2.Key([]byte(phrase), []byte("electrum"), 2048, 64, sha512.New), true)
	}
	if err := json.NewEncoder(os.Stdout).Encode(result); err != nil {
		panic(err)
	}
	fmt.Fprintln(os.Stderr, "Verified public fixture iteration", i)
}
