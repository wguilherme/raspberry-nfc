import RPi.GPIO as GPIO
import time

MOTOR_A1A = 23
MOTOR_A1B = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_A1A, GPIO.OUT)
GPIO.setup(MOTOR_A1B, GPIO.OUT)

pwm_a = GPIO.PWM(MOTOR_A1A, 100)
pwm_b = GPIO.PWM(MOTOR_A1B, 100)
pwm_a.start(30)
pwm_b.start(0)

print("Motor girando a 20% — Ctrl+C para parar")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    pwm_a.ChangeDutyCycle(0)
    pwm_b.ChangeDutyCycle(0)
    GPIO.cleanup()
    print("Motor parado")
