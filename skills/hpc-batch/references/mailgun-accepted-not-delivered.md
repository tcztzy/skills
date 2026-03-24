# Mailgun Help Center: "Troubleshooting messages marked as \"Accepted\" but not as \"Delivered\""

- Type: vendor help center article
- Author line: not listed on page
- URL: https://help.mailgun.com/hc/en-us/articles/4402879438619-Troubleshooting-messages-marked-as-Accepted-but-not-as-Delivered
- Accessed: 2026-02-22

## Why this source matters for this skill

Mailgun's event model cleanly separates "Accepted" (received/enqueued for processing) from "Delivered" (delivered to the recipient's email server). It reinforces that seeing only acceptance/queueing is not evidence of delivery.

## Relevant excerpt (verbatim, ASCII-normalized)

- "A message with an Accepted event indicates Mailgun has successfully received your message and has enqueued it for processing."
- "a Delivered event indicates Mailgun has successfully delivered your message to the recipient's email server."
