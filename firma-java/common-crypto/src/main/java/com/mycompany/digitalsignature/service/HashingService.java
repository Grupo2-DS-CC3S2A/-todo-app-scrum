package com.mycompany.digitalsignature.service;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import static pe.edu.uni.fc.cc.common.Constants.SHA_256_ALGORITHM;

/**
 * Servicio original de hash SHA-256. Se conserva calculateHash(String) y se agrega
 * calculateHash(byte[]) para firmar cualquier archivo binario: PDF, TXT, DOCX, ZIP, etc.
 */
public class HashingService {
    private MessageDigest messageDigest;

    public HashingService() {
        try {
            this.messageDigest = MessageDigest.getInstance(SHA_256_ALGORITHM);
        } catch (NoSuchAlgorithmException ex) {
            System.getLogger(HashingService.class.getName()).log(System.Logger.Level.ERROR, (String) null, ex);
        }
    }

    public BigInteger calculateHash(String message) {
        if (message == null) return null;
        return calculateHash(message.getBytes(StandardCharsets.UTF_8));
    }

    public BigInteger calculateHash(byte[] content) {
        if (content == null) return null;
        messageDigest.reset();
        byte[] digestBytes = messageDigest.digest(content);
        return new BigInteger(1, digestBytes);
    }

    public String calculateHashHex(byte[] content) {
        BigInteger hash = calculateHash(content);
        return hash == null ? null : String.format("%064x", hash);
    }
}
