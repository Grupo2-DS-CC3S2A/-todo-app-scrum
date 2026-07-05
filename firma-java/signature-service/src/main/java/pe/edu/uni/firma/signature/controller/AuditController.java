package pe.edu.uni.firma.signature.controller;

import io.swagger.v3.oas.annotations.Operation;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import pe.edu.uni.firma.signature.dto.AuditResponse;
import pe.edu.uni.firma.signature.service.DocumentSignatureFacade;

@RestController
@RequestMapping("/api/audit")
public class AuditController {
    private final DocumentSignatureFacade facade;

    public AuditController(DocumentSignatureFacade facade) {
        this.facade = facade;
    }

    @Operation(summary = "Lista auditoría de firmas y verificaciones")
    @GetMapping
    public List<AuditResponse> list() {
        return facade.audits();
    }

    @Operation(summary = "Consulta auditoría por ID")
    @GetMapping("/{id}")
    public AuditResponse findById(@PathVariable("id") Long id) {
        return facade.auditById(id);
    }

    @Operation(summary = "Elimina un registro de auditoría")
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteById(@PathVariable("id") Long id) {
        facade.deleteAudit(id);
        return ResponseEntity.noContent().build();
    }
}
