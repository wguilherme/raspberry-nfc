export default function handler(req, res) {
  const qs = req.url.includes("?") ? req.url.split("?")[1] : "";
  res.redirect(302, `http://raspberry.local:8080/callback${qs ? "?" + qs : ""}`);
}
