import React from "react";

export default function PrintMenu() {
  const handlePrint = () => {
    window.print();
  };
  return (
    <div style={{ marginBottom: 18 }}>
      <button
        className="btn"
        onClick={handlePrint}
        style={{ padding: "6px 18px", borderRadius: 8, background: "#f59e42", color: "#fff", border: 0, fontWeight: 500, cursor: "pointer" }}
      >
        Print / Save as PDF
      </button>
    </div>
  );
}
