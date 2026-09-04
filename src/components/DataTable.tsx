'use client';

import React, { useState } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  searchKey?: string;
  searchPlaceholder?: string;
  pageSize?: number;
  emptyMessage?: string;
  rowKey?: (row: T, idx: number) => string | number;
}

export default function DataTable<T extends Record<string, any>>({
  columns,
  data,
  searchKey,
  searchPlaceholder = 'FILTER RECORDS...',
  pageSize = 12,
  emptyMessage = 'NO RECORDS FOUND',
  rowKey,
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(0);

  const filteredData = React.useMemo(() => {
    if (!searchTerm || !searchKey) return data;
    return data.filter((row) =>
      String(row[searchKey] || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [data, searchTerm, searchKey]);

  const sortedData = React.useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];
      if (typeof valA === 'number' && typeof valB === 'number')
        return sortAsc ? valA - valB : valB - valA;
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredData, sortKey, sortAsc]);

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const paginatedData = sortedData.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(true); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
      {/* Search bar */}
      {searchKey && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem',
          background: '#000', border: '1px solid #2a2a2a',
          borderBottom: '1px solid #FF6600',
          padding: '0.25rem 0.5rem', marginBottom: 0,
          width: '280px',
        }}>
          <span style={{ color: '#FF6600', fontWeight: 700, fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>⌕</span>
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(0); }}
            style={{
              background: 'transparent', border: 'none', outline: 'none',
              color: '#FFFF00', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', width: '100%',
            }}
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              style={{ background: 'none', border: 'none', color: '#FF6600', cursor: 'pointer', fontSize: '0.7rem' }}
            >
              ×
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div style={{ overflowX: 'auto', border: '1px solid #2a2a2a' }}>
        <table className="bb-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{ textAlign: col.align || 'left', width: col.width }}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                >
                  {col.header}
                  {sortKey === col.key && (
                    <span style={{ marginLeft: '0.25rem', color: '#FFFF00' }}>
                      {sortAsc ? '▲' : '▼'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{
                  textAlign: 'center', padding: '1.5rem',
                  color: '#444', fontFamily: 'var(--font-mono)',
                  borderRight: 'none',
                }}>
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => (
                <tr key={rowKey ? rowKey(row, idx) : idx}>
                  {columns.map((col) => (
                    <td key={col.key} style={{ textAlign: col.align || 'left' }}>
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: '#444',
          padding: '0.3rem 0.5rem', background: '#0a0a0a',
          borderTop: '1px solid #2a2a2a', borderLeft: '1px solid #2a2a2a',
          borderRight: '1px solid #2a2a2a', borderBottom: '1px solid #2a2a2a',
        }}>
          <span style={{ color: '#666' }}>
            SHOWING {page * pageSize + 1}–{Math.min((page + 1) * pageSize, sortedData.length)} OF {sortedData.length} RECORDS
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <button
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
              style={{
                background: '#000', border: '1px solid #2a2a2a',
                padding: '0.15rem 0.5rem', color: page === 0 ? '#333' : '#FF6600',
                cursor: page === 0 ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-mono)', fontSize: '0.62rem', fontWeight: 700,
              }}
            >
              ◄ PREV
            </button>
            <span style={{ padding: '0.15rem 0.5rem', color: '#FFFF00', fontWeight: 700 }}>
              {page + 1}/{totalPages}
            </span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage(page + 1)}
              style={{
                background: '#000', border: '1px solid #2a2a2a',
                padding: '0.15rem 0.5rem', color: page >= totalPages - 1 ? '#333' : '#FF6600',
                cursor: page >= totalPages - 1 ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-mono)', fontSize: '0.62rem', fontWeight: 700,
              }}
            >
              NEXT ►
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
