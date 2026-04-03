/*
 * ============================================================
 * Fall Detection Alert System
 * Grove Vision AI V2 + Seeed Studio XIAO
 * ============================================================
 * 
 * Reads fall detection results from Grove Vision AI V2 via 
 * I2C/UART and triggers alerts (buzzer, LED, serial message).
 * 
 * Wiring:
 *   Grove Vision AI V2 → XIAO (I2C Grove connector)
 *   Buzzer → Pin D3
 *   LED    → Pin D4 (or onboard LED)
 * 
 * Author: Naron (Minh Tan Tran)
 * Project: Elderly Fall Detection System
 * ============================================================
 */

#include <Seeed_Arduino_SSCMA.h>
#include <Wire.h>

// ── Configuration ──
#define BUZZER_PIN      3
#define LED_PIN         4
#define ALERT_DURATION  5000    // Alert duration in ms
#define FALL_THRESHOLD  0.60    // Confidence threshold
#define TEMPORAL_FRAMES 5       // Frames for temporal smoothing
#define FALL_CLASS_ID   0       // Class index for "fall"

// ── SSCMA Interface ──
SSCMA AI;

// ── State tracking ──
int detectionBuffer[TEMPORAL_FRAMES] = {0};
int bufferIndex = 0;
bool alertActive = false;
unsigned long alertStartTime = 0;
unsigned long lastDetectionTime = 0;
int totalFallEvents = 0;

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    Serial.println("========================================");
    Serial.println("  Fall Detection Alert System v1.0");
    Serial.println("  Grove Vision AI V2 + XIAO");
    Serial.println("========================================");
    
    // Initialize I2C for Grove Vision AI V2
    Wire.begin();
    AI.begin();
    
    // Initialize alert pins
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    
    // Self-test
    digitalWrite(LED_PIN, HIGH);
    tone(BUZZER_PIN, 1000, 200);
    delay(300);
    digitalWrite(LED_PIN, LOW);
    
    Serial.println("System ready. Monitoring for falls...\n");
}

void loop() {
    // Invoke model inference
    if (!AI.invoke()) {
        // Process detection results
        bool fallDetectedThisFrame = false;
        
        // Check all detected boxes
        for (int i = 0; i < AI.boxes().size(); i++) {
            int classId = AI.boxes()[i].target;
            float confidence = AI.boxes()[i].score;
            
            // Log all detections
            Serial.printf("[Frame] Class: %d, Conf: %.2f, "
                         "Box: (%d,%d,%d,%d)\n",
                         classId, confidence,
                         AI.boxes()[i].x, AI.boxes()[i].y,
                         AI.boxes()[i].w, AI.boxes()[i].h);
            
            // Check for fall
            if (classId == FALL_CLASS_ID && confidence >= FALL_THRESHOLD) {
                fallDetectedThisFrame = true;
            }
        }
        
        // Update temporal buffer
        detectionBuffer[bufferIndex] = fallDetectedThisFrame ? 1 : 0;
        bufferIndex = (bufferIndex + 1) % TEMPORAL_FRAMES;
        
        // Count falls in buffer (temporal smoothing)
        int fallCount = 0;
        for (int i = 0; i < TEMPORAL_FRAMES; i++) {
            fallCount += detectionBuffer[i];
        }
        
        // Trigger alert if majority of buffer frames show fall
        bool fallConfirmed = (fallCount >= (TEMPORAL_FRAMES * 0.6));
        
        if (fallConfirmed && !alertActive) {
            triggerFallAlert();
        }
        
        // Log performance
        if (AI.perf().prepocess > 0) {
            Serial.printf("[Perf] Pre: %dms, Inf: %dms, Post: %dms\n",
                         AI.perf().prepocess,
                         AI.perf().inference,
                         AI.perf().postprocess);
        }
    }
    
    // Handle active alert
    if (alertActive) {
        updateAlert();
    }
}

void triggerFallAlert() {
    alertActive = true;
    alertStartTime = millis();
    totalFallEvents++;
    
    Serial.println("\n⚠️  ========================");
    Serial.println("⚠️  FALL DETECTED!");
    Serial.printf("⚠️  Event #%d at %lu ms\n", totalFallEvents, millis());
    Serial.println("⚠️  ========================\n");
    
    // Visual alert
    digitalWrite(LED_PIN, HIGH);
    
    // Audio alert (SOS pattern)
    playSOSPattern();
    
    // Here you would also:
    // - Send MQTT/BLE notification
    // - Trigger SMS via connected module
    // - Log to SD card
    // - Send HTTP request via WiFi module
}

void updateAlert() {
    unsigned long elapsed = millis() - alertStartTime;
    
    if (elapsed >= ALERT_DURATION) {
        // End alert
        alertActive = false;
        digitalWrite(LED_PIN, LOW);
        noTone(BUZZER_PIN);
        Serial.println("[Alert] Alert ended. Resuming monitoring.\n");
        
        // Reset buffer
        for (int i = 0; i < TEMPORAL_FRAMES; i++) {
            detectionBuffer[i] = 0;
        }
    } else {
        // Flash LED during alert
        if ((elapsed / 250) % 2 == 0) {
            digitalWrite(LED_PIN, HIGH);
        } else {
            digitalWrite(LED_PIN, LOW);
        }
    }
}

void playSOSPattern() {
    // Three short beeps
    for (int i = 0; i < 3; i++) {
        tone(BUZZER_PIN, 2000, 150);
        delay(200);
    }
    // Three long beeps
    for (int i = 0; i < 3; i++) {
        tone(BUZZER_PIN, 2000, 400);
        delay(500);
    }
    // Three short beeps
    for (int i = 0; i < 3; i++) {
        tone(BUZZER_PIN, 2000, 150);
        delay(200);
    }
}
