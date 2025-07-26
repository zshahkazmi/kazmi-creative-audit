import requests
from bs4 import BeautifulSoup
import json
import time
from fpdf import FPDF
from urllib.parse import urljoin, urlparse

PAGESPEED_API_KEY = "AIzaSyAi1FVZlnDsuSR2eDLQlKS1Bl3vfphUBcQ"  # Replace with your key

# =================== SPEED CHECK =====================
def check_page_speed(url):
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={PAGESPEED_API_KEY}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        score = data['lighthouseResult']['categories']['performance']['score'] * 100
        return score
    else:
        return None

# =================== SEO AUDIT =====================
def seo_audit(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    audit_report = {}
    audit_report['url'] = url

    # Title Tag
    title = soup.title.string if soup.title else "Missing"
    audit_report['title'] = title
    audit_report['title_length'] = len(title) if title != "Missing" else 0

    # Meta Description
    description = soup.find("meta", attrs={"name": "description"})
    audit_report['meta_description'] = description["content"] if description else "Missing"

    # H1 Tags
    h1_tags = soup.find_all("h1")
    audit_report['h1_count'] = len(h1_tags)

    # Image ALT Check
    images = soup.find_all("img")
    missing_alt = sum(1 for img in images if not img.get("alt"))
    audit_report['images_missing_alt'] = missing_alt
    audit_report['total_images'] = len(images)

    # Canonical Tag
    canonical = soup.find("link", rel="canonical")
    audit_report['canonical'] = canonical['href'] if canonical else "Missing"

    return audit_report

# =================== BROKEN LINK CHECK =====================
def check_broken_links(url):
    try:
        base_domain = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(url))
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a', href=True)]

        broken_links = []
        for link in links:
            full_url = urljoin(base_domain, link)
            try:
                res = requests.head(full_url, timeout=5)
                if res.status_code >= 400:
                    broken_links.append(full_url)
            except:
                broken_links.append(full_url)

        return broken_links
    except Exception as e:
        return []

# =================== PDF REPORT =====================
def generate_pdf_report(report, filename="seo_audit_report.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Add logo if available
    try:
        pdf.image("branding/logo.png", x=10, y=8, w=40)
    except:
        pass

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Kazmi_Creative - Website Audit Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(20)
    pdf.multi_cell(0, 10, f"Website: {report['url']}\n")
    pdf.multi_cell(0, 10, f"Page Speed Score: {report['speed_score']} / 100\n")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "SEO Audit", ln=True)
    pdf.set_font("Arial", "", 12)
    seo = report['seo_report']
    pdf.multi_cell(0, 10, f"Title: {seo['title']} (Length: {seo['title_length']} chars)")
    pdf.multi_cell(0, 10, f"Meta Description: {seo['meta_description']}")
    pdf.multi_cell(0, 10, f"H1 Tags Count: {seo['h1_count']}")
    pdf.multi_cell(0, 10, f"Images Missing ALT: {seo['images_missing_alt']} / {seo['total_images']}")
    pdf.multi_cell(0, 10, f"Canonical Tag: {seo['canonical']}")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Broken Links", ln=True)
    pdf.set_font("Arial", "", 12)
    if report['broken_links']:
        for link in report['broken_links']:
            pdf.multi_cell(0, 10, link)
    else:
        pdf.multi_cell(0, 10, "No broken links found.")

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 10, "Want to Improve Your Rankings?")
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, "Contact Kazmi_Creative for professional SEO and website optimization services.\n"
                          "Fiverr: Fiverr.com/kazmi_Creative\n"
                          "LinkedIn: Zaigham-Abbas")

    pdf.output(filename)
    return filename

# =================== MAIN =====================
def website_audit(url):
    print(f"Auditing {url} ...")
    seo = seo_audit(url)
    speed_score = check_page_speed(url)
    broken_links = check_broken_links(url)

    report = {
        "url": url,
        "speed_score": speed_score,
        "seo_report": seo,
        "broken_links": broken_links
    }
    return report

if __name__ == "__main__":
    url = input("Enter website URL: ")
    start = time.time()
    report = website_audit(url)
    print(json.dumps(report, indent=4))
    filename = generate_pdf_report(report, filename="Kazmi_Creative_Audit.pdf")
    print(f"\nReport generated: {filename}")
    print(f"Audit completed in {round(time.time()-start, 2)} seconds.")
