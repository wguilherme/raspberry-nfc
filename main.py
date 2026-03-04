import RPi.GPIO as GPIO
import time

MOTOR_A1A = 23  # ← Seu pino
MOTOR_A1B = 24  # ← Seu pino

GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_A1A, GPIO.OUT)
GPIO.setup(MOTOR_A1B, GPIO.OUT)

pwm_a = GPIO.PWM(MOTOR_A1A, 100)
pwm_b = GPIO.PWM(MOTOR_A1B, 100)
pwm_a.start(0)
pwm_b.start(0)

# Teste: aumenta devagar pra achar o RPM certo
try:
    for speed in range(0, 101, 5):
        pwm_a.ChangeDutyCycle(speed)
        pwm_b.ChangeDutyCycle(0)
        print(f"Velocidade: {speed}%")
        time.sleep(2)

    # Para o motor
    pwm_a.ChangeDutyCycle(0)
    print("Motor parado")

except KeyboardInterrupt:
    pwm_a.ChangeDutyCycle(0)
    pwm_b.ChangeDutyCycle(0)
    GPIO.cleanup()