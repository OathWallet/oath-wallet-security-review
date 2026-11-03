// Additional native-source guard tests. Only synthetic account/key data is used.
#[cfg(test)]
mod audit_rejections {
    use super::*;
    use near_sdk::test_utils::VMContextBuilder;
    use near_sdk::testing_env;
    use std::convert::TryFrom;

    fn account(name: &str) -> AccountId { name.parse().unwrap() }
    fn member(n: u8) -> MultisigMember {
        let mut bytes = vec![n; 33]; bytes[0] = 0;
        MultisigMember::AccessKey { public_key: PublicKey::try_from(bytes).unwrap() }
    }
    fn context(n: u8, timestamp: u64) {
        let public_key = match member(n) {
            MultisigMember::AccessKey { public_key } => public_key,
            _ => unreachable!(),
        };
        testing_env!(VMContextBuilder::new()
            .current_account_id(account("multisig.near"))
            .predecessor_account_id(account("multisig.near"))
            .signer_account_id(account("multisig.near"))
            .signer_account_pk(public_key)
            .account_balance(10u128.pow(30))
            .block_timestamp(timestamp).build());
    }
    fn transfer() -> MultiSigRequest {
        MultiSigRequest { receiver_id: account("recipient.near"),
            actions: vec![MultiSigRequestAction::Transfer { amount: 7.into() }] }
    }

    #[test]
    #[should_panic(expected = "This method only works when receiver_id is equal to current_account_id")]
    fn add_key_wrong_receiver_reaches_contract_guard() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2)], 1);
        let key = match member(3) { MultisigMember::AccessKey { public_key } => public_key, _ => unreachable!() };
        c.add_request_and_confirm(MultiSigRequest { receiver_id: account("recipient.near"),
            actions: vec![MultiSigRequestAction::AddKey { public_key: key, permission: None }] });
    }

    #[test]
    #[should_panic(expected = "Caller (predecessor or signer) is not a member of this multisig")]
    fn foreign_key_cannot_delete_even_after_cooldown() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2)], 2);
        let id = c.add_request(transfer());
        context(99, REQUEST_COOLDOWN + 1);
        c.delete_request(id);
    }

    #[test]
    #[should_panic(expected = "Predecessor must be a member or transaction signed with key of given account")]
    fn foreign_key_cannot_create_request() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2)], 2);
        context(99, 1);
        c.add_request(transfer());
    }

    #[test]
    #[should_panic(expected = "No such request: either wrong number or already confirmed")]
    fn member_cannot_confirm_nonexistent_request() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2)], 2);
        c.confirm(123);
    }

    #[test]
    #[should_panic(expected = "Caller (predecessor or signer) is not a member of this multisig")]
    fn removed_member_cannot_add_a_new_confirmation() {
        context(3, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2), member(3)], 2);
        let payment = c.add_request(transfer());
        context(2, 1);
        let removal = c.add_request(MultiSigRequest { receiver_id: account("multisig.near"),
            actions: vec![MultiSigRequestAction::DeleteMember { member: member(1) }] });
        drop(c.confirm(removal));
        context(3, 2);
        drop(c.confirm(removal));
        context(1, 3);
        c.confirm(payment);
    }
}
