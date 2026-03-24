# MIT OpenCourseWare (Fall 2016): M/M/1 Queue notes

## Source

- MIT OpenCourseWare, 2.854 / 2.853 *Introduction to Manufacturing Systems* (Fall 2016), handout: "M/M/1 Queue" (PDF).
- PDF: https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/927056a1af54772a587fd84ad4951e71_MIT2_854F16_Mm1Queue.pdf

## What to use from it (for this skill)

- **Stability condition:** The notes assume arrival rate `lambda < mu` (service rate). This is the "capacity exceeds demand" regime where the queue can settle to a steady state.
- **Utilization:** `rho = lambda/mu`. When rho is high, the system is near saturation.
- **Latency sensitivity (toy model):** For an M/M/1 queue, average time in system is `W = 1/(mu - lambda)` (and average number in system `L = lambda/(mu - lambda)`), so as lambda increases toward mu, waiting/latency increases sharply.
