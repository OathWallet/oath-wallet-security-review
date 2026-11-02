use secp256k1::{ecdsa::Signature, Message, PublicKey, Secp256k1};

pub(crate) fn check(der: &[u8], hash: [u8;32], point: [u8;33]) {
    let secp=Secp256k1::verification_only();
    let hash=Message::from_digest(hash);
    let point=PublicKey::from_slice(&point).unwrap();
    let verified=|sig: &Signature| secp.verify_ecdsa(&hash,sig,&point).is_ok();
    assert!(verified(&Signature::from_der(der).unwrap()));
    assert!(verified(&Signature::from_der_lax(der).unwrap()));
    let mut trailing=der.to_vec();
    trailing.push(0x42);
    let mut leading=der.to_vec();
    leading[1]+=1;
    leading[3]+=1;
    leading.insert(4,0);
    for noncanonical in [trailing,leading] {
        assert!(Signature::from_der(&noncanonical).is_err());
        assert!(verified(&Signature::from_der_lax(&noncanonical).unwrap()));
    }
    for cut in 0..der.len() {
        assert!(Signature::from_der_lax(&der[..cut]).is_err(),"truncation at {cut}");
    }
    let mut overflow=vec![0x30,0x26,2,33];
    overflow.extend([0xff;33]);
    overflow.extend([2,1,1]);
    assert!(!verified(&Signature::from_der_lax(&overflow).unwrap()));
    for malformed in [&[0x31,0x00][..], &[0x30,0xff,0x01][..], &[0x30,0x00,2,0x88,1,0,0,0,0,0,0,0][..], &[0x30,0x00,2,1,1,2,0xff][..]] {
        assert!(Signature::from_der_lax(malformed).is_err());
    }
    let mut x=0x6f617468_64657231_u64;
    let mut next=|| {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        x as u8
    };
    for i in 0..2048 {
        let len=usize::from(next())%128;
        let mut input:Vec<u8>=(0..len).map(|_| next()).collect();
        if i%2==0 && len>=4 {
            input[0]=0x30;
            input[2]=2;
        }
        if let Ok(sig)=Signature::from_der_lax(&input) {
            assert!(!verified(&sig),"unexpected signature at deterministic input {i}");
        }
    }
    println!("Verified strict and historical DER behavior, {} truncations, 2048 bounded parser inputs",der.len());
}
