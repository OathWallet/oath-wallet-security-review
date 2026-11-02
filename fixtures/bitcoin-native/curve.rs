mod der;
use std::io::{self, BufRead};
use secp256k1::{PublicKey, Scalar, Secp256k1, SecretKey};

fn bytes<const N: usize>(text: &str) -> [u8; N] {
    assert_eq!(text.len(), 2*N);
    std::array::from_fn(|i| u8::from_str_radix(&text[2*i..2*i+2], 16).unwrap())
}

fn main() {
    let args:Vec<_>=std::env::args().collect();
    if args.get(1).map(String::as_str)==Some("der") {
        assert_eq!(args.len(),5);
        let encoded:Vec<u8>=(0..args[2].len()).step_by(2).map(|i|u8::from_str_radix(&args[2][i..i+2],16).unwrap()).collect();
        der::check(&encoded,bytes(&args[3]),bytes(&args[4]));
        return
    }
    assert_eq!(args.len(),1);
    let secp = Secp256k1::new();
    let mut count = 0;
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let row: Vec<_> = line.split_whitespace().collect();
        assert_eq!(row.len(), 6);
        let secret = SecretKey::from_slice(&bytes::<32>(row[0]));
        let tweak = Scalar::from_be_bytes(bytes(row[1]));
        assert_eq!(secret.is_ok(), row[2] != "-", "scalar validity in case {count}");
        assert_eq!(tweak.is_ok(), row[3] == "valid", "tweak validity in case {count}");
        if let Ok(key) = secret {
            let point = PublicKey::from_secret_key(&secp, &key);
            assert_eq!(point.serialize(), bytes::<33>(row[2]), "public point in case {count}");
            if let Ok(tweak) = tweak {
                let child = key.add_tweak(&tweak);
                let point_child = point.add_exp_tweak(&secp, &tweak);
                assert_eq!(child.is_ok(), row[4] != "-", "private sum validity in case {count}");
                assert_eq!(point_child.is_ok(), row[5] != "-", "public sum validity in case {count}");
                if let Ok(child) = child {
                    assert_eq!(child.secret_bytes(), bytes::<32>(row[4]));
                    assert_eq!(point_child.unwrap().serialize(), bytes::<33>(row[5]));
                }
            }
        }
        count += 1;
    }
    assert_eq!(count, 137);
    println!("Verified all {count} native scalar and public point cases");
}
