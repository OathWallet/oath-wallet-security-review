// Independent offline Bitcoin address oracle for synthetic legacy TrustedCoin fixtures.
package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/btcsuite/btcd/btcec/v2"
	"github.com/btcsuite/btcd/btcutil"
	"github.com/btcsuite/btcd/btcutil/hdkeychain"
	"github.com/btcsuite/btcd/chaincfg"
)

func must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}
func main() {
	var fixture struct {
		Seeds  [2][]byte
		Legacy bool
	}
	if err := json.NewDecoder(os.Stdin).Decode(&fixture); err != nil {
		panic(err)
	}
	chain := &chaincfg.MainNetParams
	var roots []*hdkeychain.ExtendedKey
	var ids []string
	for i, s := range fixture.Seeds {
		if len(s) != 64 {
			panic("invalid synthetic seed length")
		}
		k := must(hdkeychain.NewMaster(s, chain))
		if !fixture.Legacy {
			k = must(k.Derive(hdkeychain.HardenedKeyStart + uint32(i)))
		}
		pub := must(k.Neuter())
		roots = append(roots, pub)
		ids = append(ids, pub.String())
	}
	sort.Strings(ids)
	longID := sha256.Sum256([]byte(ids[0] + ids[1]))
	// Electrum 4.6.2 trustedcoin.py get_signing_xpub, get_user_id, make_xpub.
	server := must(hdkeychain.NewKeyFromString("xpub661MyMwAqRbcGnMkaTx2594P9EDuiEqMq25PM2aeG6UmwzaohgA6uDmNsvSUV8ubqwA3Wpste1hg69XHgjUuCD5HLcEp2QPzyV1HMrPppsL"))
	parent := must(server.ECPubKey())
	h := hmac.New(sha512.New, server.ChainCode())
	h.Write(parent.SerializeCompressed())
	h.Write(longID[:])
	digest := h.Sum(nil)
	var scalar btcec.ModNScalar
	if scalar.SetByteSlice(digest[:32]) || scalar.IsZero() {
		panic("invalid fixture tweak")
	}
	var p, t, r btcec.JacobianPoint
	parent.AsJacobian(&p)
	btcec.ScalarBaseMultNonConst(&scalar, &t)
	btcec.AddNonConst(&p, &t, &r)
	r.ToAffine()
	third := btcec.NewPublicKey(&r.X, &r.Y).SerializeCompressed()
	roots = append(roots, hdkeychain.NewExtendedKey(chain.HDPublicKeyID[:], third, digest[32:], []byte{0, 0, 0, 0}, 0, 0, false))
	var keys [][]byte
	for _, k := range roots {
		child := must(must(k.Derive(0)).Derive(0))
		keys = append(keys, must(child.ECPubKey()).SerializeCompressed())
	}
	sort.Slice(keys, func(i, j int) bool { return bytes.Compare(keys[i], keys[j]) < 0 })
	script := []byte{0x52}
	for _, key := range keys {
		script = append(script, 33)
		script = append(script, key...)
	}
	script = append(script, 0x53, 0xae)
	fmt.Println(must(btcutil.NewAddressScriptHash(script, chain)).EncodeAddress())
}
