"""
Optional mitmproxy addon used only for TLS interception experiments.
This sample demonstrates where to inject or mutate headers after TLS decryption.
"""

from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    if "accept-language" not in flow.request.headers:
        flow.request.headers["accept-language"] = "en-US"
