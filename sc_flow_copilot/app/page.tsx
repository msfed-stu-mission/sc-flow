"use client";

import { useEffect, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import PDFThumbnail from "./components/file_viewer";
import "@copilotkit/react-ui/styles.css";

interface FileRetrieved {
  file_name: string;
  file_url: string;
}

interface FilesRetrieved {
  files: FileRetrieved[];
}

export default function Home() {
  const [pdfList, setPdfList] = useState<FileRetrieved[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Fetch PDF list from the server
  useEffect(() => {
    const fetchPDFs = async () => {
      try {
        const response = await fetch(`http://localhost:8000/documents/get-available-documents`);
        if (!response.ok) {
          throw new Error("Failed to fetch PDFs");
        }
        const data: FilesRetrieved = await response.json();
        setPdfList(data.files);
      } catch (error) {
        console.error("Failed to fetch PDFs:", error);
      }
    };

    fetchPDFs();
  }, []);

  // Handle opening the preview when a thumbnail is clicked
  const openPreview = (fileUrl: string) => {
    setPreviewUrl(fileUrl);
  };

  // Handle closing the preview
  const closePreview = () => {
    setPreviewUrl(null);
  };

  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="scflow">
    <div className="flex flex-col min-h-screen relative">
      {/* Header */}
      <header className="w-full bg-black text-white py-4">
        <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
          <div>
            <div className="text-2xl font-semibold">SCFlow Copilot Demo</div>
          </div>
        </div>
      </header>
  
      {/* Main Content */}
      <div className="flex flex-col items-center justify-center flex-grow px-4">
        {/* PDF Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 w-full px-4 md:px-8 lg:px-16">
          {pdfList.length > 0 ? (
            pdfList.map((pdf) => (
              <div key={pdf.file_url} className="flex flex-col items-center">
                <PDFThumbnail
                  fileUrl={pdf.file_url}
                  width={150}
                  onClick={() => openPreview(pdf.file_url)} // Open preview on thumbnail click
                />
                <div className="mt-2 text-sm text-center text-gray-700">{pdf.file_name}</div>
              </div>
            ))
          ) : (
            <div className="text-gray-500 col-span-full text-center">
              No PDFs available to display
            </div>
          )}
        </div>
  
        {/* Sidebar */}
        <div className="z-50">
          <CopilotSidebar
            defaultOpen={false}
            clickOutsideToClose={false}
            labels={{
              title: "SCFlow Copilot",
              initial: "Hi there! I am here to help co-analyze and classify your documents.",
            }}
          ></CopilotSidebar>
        </div>
      </div>
    </div>
  </CopilotKit>
  
  );
}
