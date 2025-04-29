import React from "react";

export default function PdfExportMenu() {
  const handleExportPdf = async () => {
    const jsPDF = (await import("jspdf")).default;
    const html2canvas = (await import("html2canvas")).default;
    const dashboard = document.querySelector(".dashboard-grid");
    if (!dashboard) return;
    // Clone node for clean export
    const clone = dashboard.cloneNode(true) as HTMLElement;
    clone.style.background = '#fff';
    clone.style.color = '#222';
    document.body.appendChild(clone);
    // Use html2canvas to render the dashboard grid
    const canvas = await html2canvas(clone, { backgroundColor: '#fff', scale: 2 });
    document.body.removeChild(clone);
    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    // Fit image to page
    pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
    pdf.save("analytics_dashboard.pdf");
  };
  return (
    <div style={{ marginBottom: 18 }}>
      <button
        className="btn"
        onClick={handleExportPdf}
        style={{ padding: "6px 18px", borderRadius: 8, background: "#ef4444", color: "#fff", border: 0, fontWeight: 500, cursor: "pointer" }}
      >
        Export Dashboard as PDF
      </button>
    </div>
  );
}
