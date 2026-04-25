import { ChangeEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { FileImage, Upload } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { api } from "../lib/api";

export function ScanUploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const upload = useMutation({
    mutationFn: (selected: File) => api.uploadReceipt(selected),
    onSuccess: (receipt) => navigate(`/receipts/${receipt.id}/review`),
  });

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    if (selected) upload.mutate(selected);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Scan Receipt</CardTitle>
          <FileImage size={20} />
        </CardHeader>
        <CardContent className="grid gap-5">
          <label className="flex min-h-64 cursor-pointer flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed border-ink/20 bg-white p-8 text-center transition hover:bg-cloud">
            <span className="flex h-14 w-14 items-center justify-center rounded-md bg-mint/15 text-green-800">
              <Upload size={26} />
            </span>
            <span>
              <span className="block font-semibold">Upload image or PDF</span>
              <span className="text-sm text-ink/55">Fixture mode picks a demo receipt from the file name.</span>
            </span>
            <input
              className="sr-only"
              type="file"
              accept="image/*,application/pdf"
              capture="environment"
              onChange={chooseFile}
            />
          </label>
          {file && <p className="text-sm text-ink/60">{upload.isPending ? `Processing ${file.name}` : file.name}</p>}
          {upload.error && <p className="rounded-md bg-coral/10 p-3 text-sm text-red-800">{upload.error.message}</p>}
          <Button disabled={!file || upload.isPending} onClick={() => file && upload.mutate(file)}>
            <Upload size={17} />
            {upload.isPending ? "Processing" : "Upload receipt"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

