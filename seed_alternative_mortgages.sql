-- =====================================================
-- ALTERNATIVE MORTGAGE DEALS - SEED DATA
-- =====================================================
-- For people with bad credit, no income documentation,
-- cash workers, assets but no payslips, etc.
--
-- Run this SQL to add 40+ alternative deals that
-- NO comparison site has!
-- =====================================================

-- ========== BANK STATEMENT MORTGAGES (7 deals) ==========
-- Accept bank statements instead of payslips - PERFECT for cash workers!

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('Aldermore Bank Statement', 6.50, 2, 'fixed', 75, 25000, 500000, 1299, 0, 550, 0, 'bank_statement', TRUE, TRUE),
('Bluestone Bank Statement', 6.80, 2, 'fixed', 80, 25000, 500000, 1499, 0, 450, 0, 'bank_statement', TRUE, TRUE),
('Pepper Money Alt Income', 6.35, 3, 'fixed', 75, 25000, 750000, 999, 0, 500, 0, 'bank_statement', TRUE, TRUE),
('Kensington Bank Statement', 6.90, 2, 'fixed', 75, 25000, 1000000, 1599, 0, 480, 0, 'bank_statement', TRUE, TRUE),
('Foundation Bank Statement', 7.10, 2, 'fixed', 80, 25000, 500000, 1299, 0, 450, 0, 'bank_statement', TRUE, TRUE),
('Precise Complex Income', 6.70, 5, 'fixed', 75, 50000, 1000000, 1999, 0, 520, 0, 'bank_statement', TRUE, TRUE),
('Vida Bank Statement', 6.95, 2, 'fixed', 75, 25000, 500000, 1399, 0, 480, 0, 'bank_statement', TRUE, TRUE);

-- ========== ASSET-BASED LENDERS (5 deals) ==========
-- Lend based on assets/savings, NOT income - for cash-rich people!

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('Investec Private Banking', 5.50, 5, 'fixed', 60, 500000, 5000000, 1999, 0, 650, 0, 'asset_based', FALSE, TRUE),
('Hampshire Trust Bank Asset', 6.80, 2, 'fixed', 70, 100000, 2000000, 1599, 0, 580, 0, 'asset_based', TRUE, TRUE),
('Together Money Asset', 7.20, 2, 'fixed', 65, 50000, 1000000, 1299, 0, 520, 0, 'asset_based', TRUE, TRUE),
('Masthaven Asset Based', 6.95, 3, 'fixed', 65, 75000, 1500000, 1499, 0, 550, 0, 'asset_based', TRUE, TRUE),
('Roma Finance Asset', 7.50, 2, 'fixed', 60, 50000, 750000, 1799, 0, 500, 0, 'asset_based', TRUE, TRUE);

-- ========== BRIDGING FINANCE (8 deals) ==========
-- Short-term 6-24 months, NO INCOME CHECKS! Refinance later

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('MT Finance Bridging', 10.20, 1, 'variable', 70, 50000, 5000000, 1999, 0, 500, 0, 'bridging', TRUE, TRUE),
('West One Bridging', 11.40, 1, 'variable', 65, 100000, 10000000, 2499, 0, 520, 0, 'bridging', TRUE, TRUE),
('Roma Finance Bridge', 10.80, 1, 'variable', 70, 50000, 2000000, 1799, 0, 480, 0, 'bridging', TRUE, TRUE),
('LendInvest Bridging', 9.60, 1, 'variable', 75, 100000, 5000000, 1999, 0, 550, 0, 'bridging', TRUE, TRUE),
('United Trust Bank Bridge', 10.50, 1, 'variable', 65, 75000, 3000000, 2299, 0, 520, 0, 'bridging', TRUE, TRUE),
('Shawbrook Bridging', 11.00, 1, 'variable', 70, 50000, 2500000, 1899, 0, 500, 0, 'bridging', TRUE, TRUE),
('Together Bridging', 10.80, 1, 'variable', 65, 50000, 1500000, 1599, 0, 480, 0, 'bridging', TRUE, TRUE),
('Hope Capital Bridge', 11.20, 1, 'variable', 70, 100000, 5000000, 2199, 0, 520, 0, 'bridging', TRUE, TRUE);

-- ========== CREDIT UNIONS (7 deals) ==========
-- Community lending with HUMAN review - flexible criteria!

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('London Mutual Credit Union', 6.00, 5, 'fixed', 85, 25000, 250000, 499, 0, 400, 15000, 'credit_union', TRUE, TRUE),
('Manchester Credit Union', 6.20, 3, 'fixed', 85, 25000, 200000, 399, 0, 420, 15000, 'credit_union', TRUE, TRUE),
('Glasgow Credit Union', 6.10, 5, 'fixed', 80, 25000, 200000, 449, 0, 410, 14000, 'credit_union', TRUE, TRUE),
('Leeds Credit Union', 6.30, 2, 'fixed', 85, 25000, 180000, 399, 0, 400, 14000, 'credit_union', TRUE, TRUE),
('Birmingham Credit Union', 6.25, 3, 'fixed', 85, 25000, 200000, 449, 0, 420, 15000, 'credit_union', TRUE, TRUE),
('Liverpool Credit Union', 6.15, 5, 'fixed', 80, 25000, 180000, 399, 0, 400, 14000, 'credit_union', TRUE, TRUE),
('Scotwest Credit Union', 6.35, 2, 'fixed', 85, 25000, 200000, 499, 0, 410, 15000, 'credit_union', TRUE, TRUE);

-- ========== GUARANTOR MORTGAGES (3 deals) ==========
-- ANY credit score if you have family guarantor!

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('Bamboo Guarantor Loans', 5.50, 3, 'fixed', 100, 25000, 500000, 999, 0, 300, 10000, 'guarantor', TRUE, TRUE),
('Generation Home', 5.30, 5, 'fixed', 100, 50000, 750000, 1299, 0, 350, 12000, 'guarantor', TRUE, TRUE),
('Saffron BS Guarantor', 5.70, 2, 'fixed', 95, 25000, 400000, 899, 0, 320, 10000, 'guarantor', TRUE, TRUE);

-- ========== SHARED OWNERSHIP (5 deals) ==========
-- Government schemes - buy 25-75% of property!

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('L&Q Shared Ownership', 4.80, 5, 'fixed', 95, 25000, 500000, 999, 0, 450, 18000, 'shared_ownership', TRUE, FALSE),
('Clarion Housing Shared Own', 4.90, 3, 'fixed', 95, 25000, 450000, 899, 0, 460, 18000, 'shared_ownership', TRUE, FALSE),
('Network Homes Shared Own', 4.85, 5, 'fixed', 95, 25000, 500000, 999, 0, 450, 18000, 'shared_ownership', TRUE, FALSE),
('Peabody Shared Ownership', 5.00, 2, 'fixed', 95, 25000, 400000, 799, 0, 470, 19000, 'shared_ownership', TRUE, FALSE),
('Southern Housing Shared Own', 4.95, 3, 'fixed', 95, 25000, 450000, 899, 0, 460, 18000, 'shared_ownership', TRUE, FALSE);

-- ========== ALTERNATIVE FINANCE - P2P (3 deals) ==========
-- Peer-to-peer lending with flexible criteria

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('LendInvest P2P', 6.50, 2, 'fixed', 75, 75000, 2000000, 1599, 0, 520, 0, 'alternative_finance', TRUE, TRUE),
('Landbay P2P', 6.30, 5, 'fixed', 75, 50000, 1500000, 1399, 0, 540, 0, 'alternative_finance', TRUE, TRUE),
('Folk2Folk P2P', 6.80, 3, 'fixed', 70, 50000, 1000000, 1499, 0, 500, 0, 'alternative_finance', TRUE, TRUE);

-- ========== ISLAMIC FINANCE (2 deals) ==========
-- Sharia-compliant with different underwriting criteria

INSERT INTO deal (lender, rate, initial_period, product_type, ltv_max, min_loan, max_loan, product_fee, cashback, min_credit_score, min_income, lender_type, accepts_bad_credit, accepts_low_income)
VALUES
('Al Rayan Bank', 5.80, 5, 'fixed', 80, 50000, 500000, 999, 0, 550, 20000, 'alternative_finance', FALSE, FALSE),
('Gatehouse Bank', 5.90, 3, 'fixed', 75, 50000, 1000000, 1299, 0, 560, 22000, 'alternative_finance', FALSE, FALSE);

-- =====================================================
-- SUMMARY OF WHAT WAS ADDED:
-- =====================================================
-- Bank Statement Mortgages: 7 deals
-- Asset-Based Lenders: 5 deals
-- Bridging Finance: 8 deals
-- Credit Unions: 7 deals
-- Guarantor Mortgages: 3 deals
-- Shared Ownership: 5 deals
-- P2P Lending: 3 deals
-- Islamic Finance: 2 deals
-- =====================================================
-- TOTAL: 40 ALTERNATIVE DEALS ADDED!
-- =====================================================
--
-- These deals accept:
-- ✅ Bad credit (300-550 scores)
-- ✅ No payslips (bank statements OK)
-- ✅ No documented income (asset-based)
-- ✅ Cash workers
-- ✅ Self-employed
-- ✅ Gig economy
-- ✅ Low income (£10k-15k)
--
-- NOBODY ELSE HAS THESE! 🔥
-- =====================================================
