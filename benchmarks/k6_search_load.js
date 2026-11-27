import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "15s", target: 20 },
    { duration: "30s", target: 50 },
    { duration: "15s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<150"],
  },
};

const HOT_QUERIES = ["atta", "samung", "quiet keyboard for office", "chappal", "noise cancelling"];

export default function () {
  const isHot = Math.random() < 0.8;
  const q = isHot
    ? HOT_QUERIES[Math.floor(Math.random() * HOT_QUERIES.length)]
    : `wireless keyboard model ${Math.floor(Math.random() * 10000)}`;

  const res = http.get(`http://localhost:8000/v1/search?q=${encodeURIComponent(q)}&mode=hybrid`);
  check(res, { "status is 200": (r) => r.status === 200 });
  sleep(0.1);
}
