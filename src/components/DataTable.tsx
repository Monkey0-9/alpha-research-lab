'use client';

import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Search } from 'lucide-react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  searchKey?: string;
  searchPlaceholder?: string;
  pageSize?: number;
  emptyMessage?: string;
}

export default function DataTable<T extends Record<string, any>>({
  columns,
  data,
  searchKey,
  searchPlaceholder = 'Filter records...',
  pageSize = 10,
  emptyMessage = 'No records found matching criteria'
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(0);

  // Filter
  const filteredData = React.useMemo(() => {
    if (!searchTerm || !searchKey) return data;
    return data.filter((row) =>
      String(row[searchKey] || '')
        .toLowerCase()
        .includes(searchTerm.toLowerCase())
    );
  }, [data, searchTerm, searchKey]);

  // Sort
  const sortedData = React.useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredData, sortKey, sortAsc]);

  // Paginate
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const paginatedData = sortedData.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      {searchKey && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: '#0a0d14', padding: '0.35rem 0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)', width: '280px' }}>
          <Search size={12} color="#64748b" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(0);
            }}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#f8fafc',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              width: '100%'
            }}
          />
        </div>
      )}

      <div style={{ overflowX: 'auto', border: '1px solid var(--border-terminal)', borderRadius: '3px' }}>
        <table className="terminal-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{
                    textAlign: col.align || 'left',
                    cursor: col.sortable !== false ? 'pointer' : 'default',
                    userSelect: 'none'
                  }}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                >
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span>{col.header}</span>
                    {sortKey === col.key && (
                      sortAsc ? <ChevronUp size={11} color="#38bdf8" /> : <ChevronDown size={11} color="#38bdf8" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => (
                <tr key={idx}>
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

      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
          <span>Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, sortedData.length)} of {sortedData.length} records</span>
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            <button
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
              style={{
                background: '#0d1117',
                border: '1px solid var(--border-terminal)',
                padding: '0.2rem 0.5rem',
                color: page === 0 ? '#475569' : '#94a3b8',
                borderRadius: '2px',
                cursor: page === 0 ? 'not-allowed' : 'pointer'
              }}
            >
              PREV
            </button>
            <span style={{ padding: '0.2rem 0.5rem', color: '#38bdf8' }}>PAGE {page + 1} / {totalPages}</span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage(page + 1)}
              style={{
                background: '#0d1117',
                border: '1px solid var(--border-terminal)',
                padding: '0.2rem 0.5rem',
                color: page >= totalPages - 1 ? '#475569' : '#94a3b8',
                borderRadius: '2px',
                cursor: page >= totalPages - 1 ? 'not-allowed' : 'pointer'
              }}
            >
              NEXT
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
