import React from "react";

interface ExportMenuProps {
  csvData: object[];
  fileName?: string;
}

export default function ExportMenu({ csvData, fileName = "analytics_export" }: ExportMenuProps) {
  const handleExportCSV = () => {
    if (!csvData || csvData.length === 0) return;
    const keys = Object.keys(csvData[0]);
    const csvRows = [keys.join(",")].concat(
      csvData.map(row => keys.map(k => JSON.stringify(row[k] ?? "")).join(","))
    );
    const csvContent = csvRows.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${fileName}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleExportExcel = async () => {
    if (!csvData || csvData.length === 0) return;
    // Dynamically import xlsx only when needed
    const XLSX = await import("xlsx");
    const ws = XLSX.utils.json_to_sheet(csvData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
    const wbout = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    const blob = new Blob([wbout], { type: "application/octet-stream" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${fileName}.xlsx`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div style={{ marginBottom: 18, display: "flex", gap: 12 }}>
      <button className="btn" onClick={handleExportCSV} style={{ padding: "6px 18px", borderRadius: 8, background: "#6366f1", color: "#fff", border: 0, fontWeight: 500, cursor: "pointer" }}>
        Export as CSV
      </button>
      <button className="btn" onClick={handleExportExcel} style={{ padding: "6px 18px", borderRadius: 8, background: "#10b981", color: "#fff", border: 0, fontWeight: 500, cursor: "pointer" }}>
        Export as Excel
      </button>
    </div>
  );
}
