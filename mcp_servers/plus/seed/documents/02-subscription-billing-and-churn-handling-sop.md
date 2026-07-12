# Subscription Billing and Churn Handling SOP — MCN+

## Purpose

This document defines MCN+ streaming's subscription tiers, billing/dunning
process, and the retention process applied when a subscriber attempts to
cancel.

## Subscription Tiers

- **Basic**: ad-supported, single-device streaming, standard definition.
- **Standard**: ad-light (limited pre-roll only), two concurrent devices,
  full HD.
- **Premium**: ad-free, four concurrent devices, full HD + select 4K
  titles, offline downloads.

Billing is monthly or annual (annual pays 2 months' equivalent for a
12-month term, a discount versus paying monthly).

## Billing and Dunning Process

1. Subscription Ops charges the subscriber's payment method on the
   billing anniversary date.
2. If a charge fails, the subscriber enters a **grace period**: access
   continues for 3 days while up to 2 automatic retries occur (24 hours
   apart).
3. If both retries fail, the account is downgraded to a restricted state
   (playback paused, account/profile data retained) and the subscriber is
   notified by email and in-app banner.
4. An account in restricted state for more than 30 days without a
   successful payment is auto-cancelled, and its subscriber count is
   removed from active-subscriber reporting as of the restriction date
   (not the 30-day mark).

## Cancellation and Retention Flow

1. A subscriber-initiated cancellation request first routes through an
   in-app retention flow: a discounted-tier offer (Subscription Ops sets
   the current offer terms) is presented before the cancellation is
   confirmed.
2. If the subscriber proceeds past the retention offer, the cancellation
   is confirmed immediately, but access continues until the end of the
   current paid billing period (no partial refunds for the unused
   portion, standard for subscription services).
3. Cancellations flagged as involuntary (failed payment, per the dunning
   process above) are logged separately from voluntary cancellations in
   churn reporting, since they require different retention tactics (a
   billing fix, not a retention offer).
4. Subscription Ops reviews the voluntary-cancellation reason (collected
   via a short exit survey) monthly to identify recurring churn drivers
   for the Programming Committee.
