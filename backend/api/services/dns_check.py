import dns.resolver
import dns.exception


async def check_domain_dns(domain: str):
    result = {
        "mx_verified": False,
        "spf_verified": False,
        "dkim_verified": False,
        "mx_record": None,
        "spf_record": None,
        "dkim_record": None,
        "dkim_selector": "default",
    }

    # MX check
    try:
        mx_answers = dns.resolver.resolve(domain, "MX")
        for rdata in mx_answers:
            result["mx_record"] = str(rdata.exchange)
            result["mx_verified"] = True
            break
    except (dns.exception.DNSException, Exception):
        pass

    # SPF check
    try:
        txt_answers = dns.resolver.resolve(domain, "TXT")
        for rdata in txt_answers:
            txt = "".join([s.decode() if isinstance(s, bytes) else s for s in rdata.strings])
            if txt.startswith("v=spf1"):
                result["spf_record"] = txt
                result["spf_verified"] = True
                break
    except (dns.exception.DNSException, Exception):
        pass

    # DKIM check
    try:
        dkim_answers = dns.resolver.resolve(f"default._dkim.{domain}", "TXT")
        for rdata in dkim_answers:
            txt = "".join([s.decode() if isinstance(s, bytes) else s for s in rdata.strings])
            if txt.startswith("v=DKIM1"):
                result["dkim_record"] = txt
                result["dkim_verified"] = True
                break
    except (dns.exception.DNSException, Exception):
        pass

    return result
