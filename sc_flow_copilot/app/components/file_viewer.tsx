import React, { useEffect, useRef, useState } from "react";
import { getDocument, GlobalWorkerOptions, PDFDocumentProxy } from "pdfjs-dist";

// Set the worker source to the locally hosted file
GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

interface PDFThumbnailProps {
  fileUrl: string;
  width?: number;
  onClick?: () => void;
}

interface FileSelected {
  file_url: string;
}

// Utility to post data to the server
const postFileSelection = async (data: FileSelected) => {
  try {
    await fetch("http://localhost:8000/documents/document-selected", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
  } catch (error) {
    console.error("Failed to post file selection:", error);
  }
};

const PDFThumbnail: React.FC<PDFThumbnailProps> = ({ fileUrl, width = 200 }) => {
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [showFullPDF, setShowFullPDF] = useState(false); // State to control full PDF preview
  const [contextMenuPosition, setContextMenuPosition] = useState<{ x: number; y: number } | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null); // Reference for sidebar

  // Extract file name from URL
  const fileName = fileUrl.split("/").pop() || "Unknown File";

  useEffect(() => {
    const renderThumbnail = async () => {
      try {
        const pdf: PDFDocumentProxy = await getDocument(fileUrl).promise;
        const firstPage = await pdf.getPage(1);

        const viewport = firstPage.getViewport({ scale: 1 });
        const canvas = canvasRef.current;

        if (canvas) {
          const context = canvas.getContext("2d");
          const scale = width / viewport.width; // Scale the page to fit the desired width
          const scaledViewport = firstPage.getViewport({ scale });

          canvas.width = scaledViewport.width;
          canvas.height = scaledViewport.height;

          await firstPage.render({
            canvasContext: context!,
            viewport: scaledViewport,
          }).promise;

          setThumbnailUrl(canvas.toDataURL("image/png"));
        }
      } catch (error) {
        console.error("Failed to render PDF thumbnail:", error);
      }
    };

    renderThumbnail();
  }, [fileUrl, width]);

  // Handle right-click (context menu)
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenuPosition({ x: e.pageX, y: e.pageY });
  };

  // Handle menu option click
  const handleMenuOptionClick = () => {
    setShowFullPDF(true);
    setContextMenuPosition(null); // Close context menu

    // Notify server of the selected file
    postFileSelection({ file_url: fileUrl });
  };

  // Handle clicking outside the modal to close it
  const handleModalBackgroundClick = (e: React.MouseEvent) => {
    if (
      modalRef.current &&
      !modalRef.current.contains(e.target as Node) &&
      sidebarRef.current &&
      !sidebarRef.current.contains(e.target as Node)
    ) {
      setShowFullPDF(false);

      // Notify server of the closed file
      postFileSelection({ file_url: "" });
    }
  };

  return (
    <div>
      <div
        className="relative"
        onContextMenu={handleContextMenu}
        style={{ cursor: "context-menu" }}
      >
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt="PDF Thumbnail"
            className="border rounded shadow-md"
            style={{ width }}
          />
        ) : (
          <p>Loading ...</p>
        )}
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      {/* Context Menu */}
      {contextMenuPosition && (
        <div
          className="absolute bg-white border shadow-md rounded z-10"
          style={{
            top: contextMenuPosition.y,
            left: contextMenuPosition.x,
          }}
        >
          <button
            className="block px-4 py-2 text-left w-full hover:bg-gray-200"
            onClick={handleMenuOptionClick}
          >
            View Full PDF
          </button>
        </div>
      )}

      {/* Full PDF Preview */}
      {showFullPDF && (
        <div
          className="fixed inset-0 flex z-50"
          //onClick={handleModalBackgroundClick} // Close on background click
        >
          {/* Left side (greyed out background) */}
          <div
            className="bg-black bg-opacity-75 w-3/4 flex justify-center items-center relative z-50"
            onClick={(e) => e.stopPropagation()} // Prevent background click from closing modal
            style={{ zIndex: 51 }} // Ensure modal background sits under the sidebar
          >
            {/* Floating Close Icon */}
            <button
              className="relative left-0 -translate-y-5 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-full p-2 shadow-md z-9"
              onClick={() => {
                setShowFullPDF(false);

                // Notify server of the closed file
                postFileSelection({ file_url: "" });
              }} // Close modal
              style={{ position: "absolute" }}
            >
              ✕
            </button>

            <div
              ref={modalRef}
              className="relative bg-white w-3/4 h-3/4 overflow-auto rounded shadow-lg z-50"
            >
              <PDFPreview fileUrl={fileUrl} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Full PDF Preview Component
const PDFPreview: React.FC<{ fileUrl: string }> = ({ fileUrl }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderFullPDF = async () => {
      const pdf = await getDocument(fileUrl).promise;
      const container = containerRef.current;

      if (container) {
        container.innerHTML = ""; // Clear any previous render
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const viewport = page.getViewport({ scale: 1.5 });

          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d")!;
          canvas.width = viewport.width;
          canvas.height = viewport.height;

          await page.render({
            canvasContext: context,
            viewport,
          }).promise;

          container.appendChild(canvas);
        }
      }
    };

    renderFullPDF();
  }, [fileUrl]);

  return <div ref={containerRef} className="p-4" />;
};

export default PDFThumbnail;
