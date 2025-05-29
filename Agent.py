class user:
    def __init__(self,name,id ,password,age,gender,phoneNum,
                 email, adress, familyStatus, AIProfile):
        self.name=name
        self.id=id
        self.password=password
        self.age=age
        self.gender=gender
        self.phoneNum=phoneNum
        self.email=email
        self.adress=adress
        self.familyStatus=familyStatus
        self.AIProfile=AIProfile
    def getName(self):
        return self.name
    def isPassword(self, password):
        return self.password == password
    def getAIProfile(self):
        return self.AIProfile
    def getUser(self, id):
        if id == self.id:
            return self

class ServiceProvider:
    def __init__(self, name, phoneNum, email, gender, id, password
                 , ClinicAdress, profession, ProfessionValidation
                 ,AIProfile ):
        self.name=name
        self.phoneNum=phoneNum
        self.email=email
        self.gender=gender
        self.id=id
        self.password=password
        self.ClinicAdress=ClinicAdress
        self.profession=profession
        self.ProfessionValidation=ProfessionValidation
        self.AIProfile=AIProfile
        self.AdminValidation = True
    def getName(self):
        return self.name
    def isPassword(self, password):
        return self.password == password
    def getClinicAdress(self):
        return self.ClinicAdress
    def getProfession(self):
        return self.profession
    def getProfessionValidation(self):
        return self.ProfessionValidation
    def getAIProfile(self):
        return self.AIProfile
    def getAdminValidation(self):
        return self.AdminValidation
    


