import type { CmsBlock } from '@/lib/types';

type Props = {
  blocks: CmsBlock[];
};

function clampHeading(level?: number): 2 | 3 | 4 {
  if (level === 3 || level === 4) return level;
  return 2;
}

export default function CmsBlocks({ blocks }: Props) {
  return (
    <div className='cms-blocks'>
      {blocks.map((block, idx) => {
        if (block.type === 'heading') {
          const level = clampHeading(block.level);
          if (level === 3) return <h3 key={idx}>{block.text || ''}</h3>;
          if (level === 4) return <h4 key={idx}>{block.text || ''}</h4>;
          return <h2 key={idx}>{block.text || ''}</h2>;
        }

        if (block.type === 'paragraph') {
          return <p key={idx}>{block.text || ''}</p>;
        }

        if (block.type === 'callout') {
          return (
            <aside key={idx} className='cms-callout'>
              {block.title ? <strong>{block.title}</strong> : null}
              <p>{block.text || ''}</p>
            </aside>
          );
        }

        if (block.type === 'list') {
          const items = block.items || [];
          if (block.style === 'ordered') {
            return (
              <ol key={idx}>
                {items.map((item, itemIdx) => (
                  <li key={itemIdx}>{item}</li>
                ))}
              </ol>
            );
          }
          return (
            <ul key={idx}>
              {items.map((item, itemIdx) => (
                <li key={itemIdx}>{item}</li>
              ))}
            </ul>
          );
        }

        if (block.type === 'table') {
          return (
            <figure key={idx} className='cms-table-wrap'>
              {block.caption ? <figcaption>{block.caption}</figcaption> : null}
              <table className='cms-table'>
                <thead>
                  <tr>
                    {(block.headers || []).map((header, hIdx) => (
                      <th key={hIdx}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(block.rows || []).map((row, rIdx) => (
                    <tr key={rIdx}>
                      {row.map((cell, cIdx) => (
                        <td key={cIdx}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </figure>
          );
        }

        if (block.type === 'divider') {
          return <hr key={idx} className='cms-divider' />;
        }

        if (block.type === 'link') {
          return (
            <p key={idx}>
              <a href={block.href || '#'}>{block.text || 'Read more'}</a>
            </p>
          );
        }

        return null;
      })}
    </div>
  );
}
