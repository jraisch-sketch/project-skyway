import './globals.css';
import 'leaflet/dist/leaflet.css';
import Link from 'next/link';
import HeaderNav from '@/components/HeaderNav';
import { serverApiFetch } from '@/lib/serverApi';
import type { CmsNavigation } from '@/lib/types';

export const metadata = {
  title: 'Skyway | Collegiate Cycling Finder',
  description: 'Find college cycling programs by map and filters',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const topNav = await serverApiFetch<CmsNavigation>('/cms/navigations/main-top-nav/');
  const footerNav = await serverApiFetch<CmsNavigation>('/cms/navigations/main-footer-nav/');
  const initialPrimaryLinks =
    topNav?.items?.map((item) => ({
      href: item.page_slug ? `/content/${item.page_slug}` : (item.external_url || '#'),
      label: item.title,
      openInNewTab: item.open_new_tab,
    })) || [];
  const footerLinks =
    footerNav?.items?.map((item) => ({
      href: item.page_slug ? `/content/${item.page_slug}` : (item.external_url || '#'),
      label: item.title,
      openInNewTab: item.open_new_tab,
    })) || [
      { href: '/content/about-skyway', label: 'About', openInNewTab: false },
      { href: '/content/contact-us', label: 'Contact', openInNewTab: false },
      { href: '/schools/table-of-contents', label: 'School Table of Contents', openInNewTab: false },
    ];

  return (
    <html lang="en">
      <body>
        <header className="header">
          <div className="container nav">
            <Link href="/" className="brand" aria-label="Skyway home">
              <img src="/skyway-logo.png" alt="Skyway Collegiate Cycling Finder" className="brand-logo" />
              <span className="brand-title">
                <span>Skyway</span>
                <span>Collegiate Cycling Finder</span>
              </span>
            </Link>
            <HeaderNav initialPrimaryLinks={initialPrimaryLinks} />
          </div>
        </header>
        <main className="container">{children}</main>
        <footer className="footer">
          <div className="container footer-inner">
            <div className="footer-nav">
              {footerLinks.map((link) =>
                link.href.startsWith('http://') || link.href.startsWith('https://') ? (
                  <a
                    key={link.href}
                    href={link.href}
                    target={link.openInNewTab ? '_blank' : undefined}
                    rel={link.openInNewTab ? 'noreferrer noopener' : undefined}
                  >
                    {link.label}
                  </a>
                ) : (
                  <Link key={link.href} href={link.href}>
                    {link.label}
                  </Link>
                )
              )}
            </div>
            <div className="footer-powered">
              <span>Powered by</span>
              <img src="/yjr-outdoors-logo.png" alt="YJR Outdoors" className="footer-powered-logo" />
              <span>YJR Outdoors</span>
            </div>
            <p className="footer-disclaimer">
              Data shown on this site is aggregated from publicly available sources and automated enrichment
              services. Sources include institutional websites, public webpages, USA Cycling public materials,
              NCES/IPEDS datasets (ArcGIS), OpenStreetMap Nominatim, and the U.S. Department of Education
              College Scorecard API (Data.gov). Information is periodically refreshed and may not reflect the
              latest changes.
            </p>
            <p className="footer-copyright">Copyright YJR Outdoors LLC</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
