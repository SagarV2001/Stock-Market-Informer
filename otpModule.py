import random
rand = random.Random()
def generateOTP(length):
    otp=""
    for i in range(length):
        otp+=str(rand.randint(0,9))
    return otp