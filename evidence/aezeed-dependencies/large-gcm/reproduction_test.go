package primitiveaudit
import("testing";"crypto/aes";"crypto/cipher";"bytes";"gitlab.com/yawning/bsaes.git/ct64")
func TestLargeAAD(t *testing.T){
 key:=make([]byte,16);nonce:=make([]byte,12);ad:=make([]byte,1<<29)
 standard,_:=aes.NewCipher(key);reference,_:=cipher.NewGCM(standard)
 candidate,_:=ct64.NewCipher(key).(interface{NewGCM(int)(cipher.AEAD,error)}).NewGCM(12)
 expected:=reference.Seal(nil,nonce,nil,ad);actual:=candidate.Seal(nil,nonce,nil,ad)
 if bytes.Equal(actual,expected){t.Fatal("expected documented length truncation to differ")}
 if _,err:=reference.Open(nil,nonce,actual,ad);err==nil{t.Fatal("standard GCM unexpectedly accepted truncated-length tag")}
 t.Log("Reproduced 512 MiB AAD tag mismatch; no plaintext and no production inputs")
}
