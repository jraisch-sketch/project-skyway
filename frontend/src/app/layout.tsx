import './globals.css';
import 'leaflet/dist/leaflet.css';
import Link from 'next/link';

export const metadata = {
  title: 'Project Skyway',
  description: 'Find college cycling programs by map and filters',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="header">
          <div className="container nav">
            <Link href="/" className="brand">Project Skyway</Link>
            <nav className="nav-links">
              <Link href="/">Search</Link>
              <Link href="/login">Login</Link>
              <Link href="/register">Register</Link>
            </nav>
          </div>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
