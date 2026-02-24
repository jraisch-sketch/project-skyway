import { notFound } from 'next/navigation';

import CmsBlocks from '@/components/CmsBlocks';
import { serverApiFetch } from '@/lib/serverApi';
import type { CmsNavItem, CmsPage, CmsWidgetPlacement } from '@/lib/types';

type Params = {
  slug: string;
};

function navHref(item: CmsNavItem): string {
  if (item.page_slug) {
    return `/content/${item.page_slug}`;
  }
  return item.external_url || '#';
}

function NavTree({ items }: { items: CmsNavItem[] }) {
  if (!items.length) return null;

  return (
    <ul className='cms-nav-tree'>
      {items.map((item) => {
        const href = navHref(item);
        return (
          <li key={item.id}>
            <a href={href} target={item.open_new_tab ? '_blank' : undefined} rel={item.open_new_tab ? 'noreferrer noopener' : undefined}>
              {item.title}
            </a>
            <NavTree items={item.children || []} />
          </li>
        );
      })}
    </ul>
  );
}

function slotWidgets(widgets: CmsWidgetPlacement[], slot: CmsWidgetPlacement['slot']) {
  return widgets.filter((entry) => entry.slot === slot);
}

export default async function CmsPageRoute({ params }: { params: Params }) {
  const page = await serverApiFetch<CmsPage>(`/cms/pages/${params.slug}/`);
  if (!page) {
    notFound();
  }

  const topWidgets = slotWidgets(page.widgets || [], 'content_top');
  const bottomWidgets = slotWidgets(page.widgets || [], 'content_bottom');
  const sidebarWidgets = slotWidgets(page.widgets || [], 'sidebar');

  return (
    <div className='cms-page-shell'>
      {page.navigation?.items?.length ? (
        <nav className='cms-secondary-topnav' aria-label='Section navigation'>
          {page.navigation.items.map((item) => (
            <a
              key={item.id}
              href={navHref(item)}
              target={item.open_new_tab ? '_blank' : undefined}
              rel={item.open_new_tab ? 'noreferrer noopener' : undefined}
            >
              {item.title}
            </a>
          ))}
        </nav>
      ) : null}

      <div className='cms-layout'>
        <article className='cms-main panel'>
          {page.show_title ? <h1>{page.title}</h1> : null}
          {page.summary ? <p className='cms-summary'>{page.summary}</p> : null}

          {topWidgets.map((entry) => (
            <section key={entry.id} className='cms-widget panel'>
              {entry.widget.title ? <h3>{entry.widget.title}</h3> : null}
              <CmsBlocks blocks={entry.widget.body || []} />
            </section>
          ))}

          <CmsBlocks blocks={page.body || []} />

          {bottomWidgets.map((entry) => (
            <section key={entry.id} className='cms-widget panel'>
              {entry.widget.title ? <h3>{entry.widget.title}</h3> : null}
              <CmsBlocks blocks={entry.widget.body || []} />
            </section>
          ))}
        </article>

        {(page.show_sidebar_navigation || sidebarWidgets.length > 0) ? (
          <aside className='cms-sidebar'>
            {page.show_sidebar_navigation && page.navigation?.items?.length ? (
              <section className='panel'>
                <h3>{page.navigation.name}</h3>
                <NavTree items={page.navigation.items} />
              </section>
            ) : null}

            {sidebarWidgets.map((entry) => (
              <section key={entry.id} className='panel'>
                {entry.widget.title ? <h3>{entry.widget.title}</h3> : null}
                <CmsBlocks blocks={entry.widget.body || []} />
              </section>
            ))}
          </aside>
        ) : null}
      </div>
    </div>
  );
}
