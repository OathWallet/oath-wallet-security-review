// Appended only to an isolated, hash-bound copy of the upstream contract source.
// Mock receipts describe scheduled actions; they do not execute a blockchain.
#[cfg(test)]
mod audit_contract {
    use super::*;
    use near_sdk::test_utils::{get_created_receipts, VMContextBuilder};
    use near_sdk::mock::VmAction;
    use near_sdk::testing_env;
    use std::convert::TryFrom;

    fn account(name: &str) -> AccountId { name.parse().unwrap() }
    fn key(n: u8) -> PublicKey {
        let mut bytes = vec![n; 33]; bytes[0] = 0;
        PublicKey::try_from(bytes).unwrap()
    }
    fn member(n: u8) -> MultisigMember {
        MultisigMember::AccessKey { public_key: key(n) }
    }
    fn context(n: u8, timestamp: u64) {
        testing_env!(VMContextBuilder::new()
            .current_account_id(account("multisig.near"))
            .predecessor_account_id(account("multisig.near"))
            .signer_account_id(account("multisig.near"))
            .signer_account_pk(key(n))
            .account_balance(10u128.pow(30))
            .block_timestamp(timestamp).build());
    }
    fn transfer(amount: u128) -> MultiSigRequest {
        MultiSigRequest { receiver_id: account("recipient.near"),
            actions: vec![MultiSigRequestAction::Transfer { amount: amount.into() }] }
    }

    #[test]
    fn quorum_schedules_exact_transfer_and_cleans_request() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2), member(3)], 2);
        context(1, 1);
        let id = c.add_request(transfer(987654321));
        drop(c.confirm(id));
        assert!(get_created_receipts().is_empty());
        assert_eq!(c.get_confirmations(id), vec![member(1).to_string()]);
        context(2, 2);
        drop(c.confirm(id));
        let receipts = get_created_receipts();
        assert_eq!(receipts.len(), 1);
        assert_eq!(receipts[0].receiver_id, account("recipient.near"));
        assert_eq!(receipts[0].actions, vec![VmAction::Transfer { deposit: 987654321 }]);
        assert!(c.list_request_ids().is_empty());
        assert!(c.confirmations.get(&id).is_none());
        assert_eq!(c.get_num_requests_per_member(member(1)), 0);
    }

    #[test]
    fn quorum_preserves_function_call_bytes_deposit_and_gas() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2)], 2);
        context(1, 1);
        let args = br#"{"receiver_id":"recipient.near","amount":"12345678901234567890"}"#.to_vec();
        let id = c.add_request(MultiSigRequest { receiver_id: account("token.near"),
            actions: vec![MultiSigRequestAction::FunctionCall {
                method_name: "ft_transfer".to_string(), args: args.clone().into(),
                deposit: 1.into(), gas: 10_000_000_000_000u64.into() }] });
        drop(c.confirm(id));
        assert!(get_created_receipts().is_empty());
        context(2, 2);
        drop(c.confirm(id));
        let receipts = get_created_receipts();
        assert_eq!(receipts.len(), 1);
        assert_eq!(receipts[0].receiver_id, account("token.near"));
        assert_eq!(receipts[0].actions, vec![VmAction::FunctionCall {
            method_name: "ft_transfer".to_string(), args,
            deposit: 1, gas: Gas(10_000_000_000_000) }]);
    }

    #[test]
    fn cooldown_cleanup_preserves_other_members_requests() {
        context(1, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2)], 2);
        let first = c.add_request(transfer(1));
        context(2, 0);
        let second = c.add_request(transfer(2));
        context(1, REQUEST_COOLDOWN + 1);
        c.delete_request(first);
        assert_eq!(c.list_request_ids(), vec![second]);
        assert_eq!(c.get_num_requests_per_member(member(1)), 0);
        assert_eq!(c.get_num_requests_per_member(member(2)), 1);
        assert!(c.confirmations.get(&first).is_none());
        assert!(get_created_receipts().is_empty());
    }

    #[test]
    fn characterizes_confirmation_retained_after_quorum_authorized_member_removal() {
        context(3, 0);
        let mut c = MultiSigContract::new(vec![member(1), member(2), member(3)], 2);
        let payment = c.add_request(transfer(7));
        context(1, 1);
        drop(c.confirm(payment));
        context(2, 2);
        let removal = c.add_request(MultiSigRequest { receiver_id: account("multisig.near"),
            actions: vec![MultiSigRequestAction::DeleteMember { member: member(1) }] });
        drop(c.confirm(removal));
        context(3, 3);
        drop(c.confirm(removal));
        assert_eq!(c.get_members().len(), 2);
        assert!(!c.get_members().contains(&member(1)));
        assert_eq!(c.get_confirmations(payment), vec![member(1).to_string()]);
        context(1, 4);
        assert!(c.current_member().is_none());
        context(2, 5);
        drop(c.confirm(payment));
        let receipts = get_created_receipts();
        assert_eq!(receipts.len(), 1);
        assert_eq!(receipts[0].actions, vec![VmAction::Transfer { deposit: 7 }]);
        assert!(c.list_request_ids().is_empty());
    }
}
