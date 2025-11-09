import json
import os
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fpdf import FPDF

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY")

# =================== SPEED CHECK =====================
def check_page_speed(url):
    """Return the Google PageSpeed score for the supplied URL.

    The request is skipped when no API key is configured so the rest of the
    audit can still complete successfully.
    """

    if not PAGESPEED_API_KEY:
        return None

    params = {"url": url, "key": PAGESPEED_API_KEY}
    try:
        response = requests.get(
            "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        score = (
            data["lighthouseResult"]["categories"]["performance"]["score"] * 100
        )
        return round(score)
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None

# =================== SEO AUDIT =====================
def seo_audit(url):
    """Collect on-page SEO information for the supplied URL."""

    audit_report = {
        "url": url,
        "title": "Missing",
        "title_length": 0,
        "meta_description": "Missing",
        "h1_count": 0,
        "images_missing_alt": 0,
        "total_images": 0,
        "canonical": "Missing",
    }

    try:
        response = requests.get(url, timeout=15, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except requests.RequestException:
        return audit_report

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.title.string.strip() if soup.title and soup.title.string else "Missing"
    audit_report["title"] = title_tag
    audit_report["title_length"] = len(title_tag) if title_tag != "Missing" else 0

    description = soup.find("meta", attrs={"name": "description"})
    if description and description.get("content"):
        audit_report["meta_description"] = description["content"].strip()

    h1_tags = soup.find_all("h1")
    audit_report["h1_count"] = len(h1_tags)

    images = soup.find_all("img")
    audit_report["total_images"] = len(images)
    audit_report["images_missing_alt"] = 0
    for img in images:
        alt_text = img.get("alt")
        if not (alt_text and alt_text.strip()):
            audit_report["images_missing_alt"] += 1

    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        audit_report["canonical"] = canonical["href"]

    return audit_report

# =================== BROKEN LINK CHECK =====================
def check_broken_links(url):
    """Return a list of broken links found on the supplied URL."""

    try:
        base_domain = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(url))
        response = requests.get(url, timeout=15, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = [a.get("href") for a in soup.find_all("a", href=True)]

    broken_links = []
    for link in links:
        full_url = urljoin(base_domain, link)
        try:
            res = requests.head(full_url, timeout=10, allow_redirects=True, headers=DEFAULT_HEADERS)
            if res.status_code >= 400:
                raise requests.RequestException
        except requests.RequestException:
            try:
                res = requests.get(full_url, timeout=15, headers=DEFAULT_HEADERS)
                if res.status_code >= 400:
                    broken_links.append(full_url)
            except requests.RequestException:
                broken_links.append(full_url)

    return sorted(set(broken_links))

# =================== PDF REPORT =====================
def generate_pdf_report(report, filename=None, output_dir="reports"):
    """Generate a PDF report and return the path to the generated file."""

    os.makedirs(output_dir, exist_ok=True)

    if not filename:
        parsed_url = urlparse(report.get("url", "website"))
        site_name = parsed_url.netloc or parsed_url.path or "website"
        site_name = site_name.replace(":", "_").replace("/", "_")
        filename = f"{site_name}_{int(time.time())}_audit.pdf"

    output_path = os.path.join(output_dir, filename)

    pdf = FPDF()
    pdf.add_page()

    try:
        pdf.image("static/logo.png", x=10, y=8, w=40)
    except Exception:
        pass

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Kazmi_Creative - Website Audit Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(20)
    pdf.multi_cell(0, 8, f"Website: {report.get('url', 'N/A')}")

    speed_score = report.get("speed_score")
    speed_text = f"{speed_score} / 100" if speed_score is not None else "Not available"
    pdf.multi_cell(0, 8, f"Page Speed Score: {speed_text}")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "SEO Audit", ln=True)
    pdf.set_font("Arial", "", 12)
    seo = report.get("seo_report", {})
    pdf.multi_cell(0, 8, f"Title: {seo.get('title', 'Missing')} (Length: {seo.get('title_length', 0)} chars)")
    pdf.multi_cell(0, 8, f"Meta Description: {seo.get('meta_description', 'Missing')}")
    pdf.multi_cell(0, 8, f"H1 Tags Count: {seo.get('h1_count', 0)}")
    pdf.multi_cell(0, 8, f"Images Missing ALT: {seo.get('images_missing_alt', 0)} / {seo.get('total_images', 0)}")
    pdf.multi_cell(0, 8, f"Canonical Tag: {seo.get('canonical', 'Missing')}")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Broken Links", ln=True)
    pdf.set_font("Arial", "", 12)
    broken_links = report.get("broken_links", [])
    if broken_links:
        for link in broken_links:
            pdf.multi_cell(0, 8, link)
    else:
        pdf.multi_cell(0, 8, "No broken links found.")

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 8, "Want to Improve Your Rankings?")
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(
        0,
        8,
        "Contact Kazmi_Creative for professional SEO and website optimization services.\n"
        "Fiverr: Fiverr.com/kazmi_Creative\n"
        "LinkedIn: Zaigham-Abbas",
    )

    pdf.output(output_path)
    return output_path

# =================== MAIN =====================
def audit_website(url):
    """Run the full website audit workflow for the supplied URL."""

    seo = seo_audit(url)
    speed_score = check_page_speed(url)
    broken_links = check_broken_links(url)

    return {
        "url": url,
        "speed_score": speed_score,
        "seo_report": seo,
        "broken_links": broken_links,
    }


def website_audit(url):
    """Backward compatible wrapper for previous CLI usage."""

    return audit_website(url)

if __name__ == "__main__":
    url = input("Enter website URL: ")
    start = time.time()
    report = website_audit(url)
    print(json.dumps(report, indent=4))
    filename = generate_pdf_report(report, filename="Kazmi_Creative_Audit.pdf")
    print(f"\nReport generated: {filename}")
    print(f"Audit completed in {round(time.time()-start, 2)} seconds.")
