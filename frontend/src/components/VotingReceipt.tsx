import type { ReactElement } from "react";

import type { VotoCifrado } from "@/types/voting";

export interface VotingReceiptProps {
  readonly comprobante: VotoCifrado;
}

function formatTimestamp(epoch: number): string {
  return new Date(epoch * 1000).toISOString();
}

export function VotingReceipt({ comprobante }: VotingReceiptProps): ReactElement {
  return (
    <div className="voting-receipt" role="status">
      <h3>Voto Procesado Exitosamente</h3>
      <p>Tu voto ha sido cifrado y es anonimo.</p>
      <div className="receipt-code">
        <p>
          <strong>Hash Cifrado:</strong> {comprobante.hash_voto}
        </p>
        <p>
          <strong>Llave Genetica:</strong> {comprobante.clave_genetica}
        </p>
        <p>
          <strong>Timestamp:</strong> {formatTimestamp(comprobante.timestamp)}
        </p>
      </div>
    </div>
  );
}
