from template.control import *
from utils.timer import Timer


class Character:
    def __init__(self, id, device, e_cd, q_cd):
        self.id = id
        self.device = device
        self.e_cd = e_cd
        self.q_cd = q_cd

        self.e_timer = Timer(self.e_cd).force_reached()
        self.q_timer = Timer(self.q_cd).force_reached()

    @property
    def is_e_ready(self):
        return self.e_timer.reached
    
    @property
    def is_q_ready(self):
        return self.q_timer.reached

    @property
    def is_a_ready(self):
        return True

    def use_e(self):
        self.device.click(SKILL_E)
        self.e_timer.reset()
        self.device.sleep((0.4, 0.6))

    def use_q(self):
        self.device.click(SKILL_Q)
        self.q_timer.reset()
        self.device.sleep((5.9, 6.1))

    def use_a(self):
        self.device.click(BA)
        self.device.sleep((0.1, 0.2))

    def use(self, type):
        type = type.upper()
        if type == 'E':
            self.use_e()
        elif type == 'Q':
            self.use_q()
        elif type == 'A':
            self.use_a()
        else:
            raise ValueError('Illegal type')

    def is_ready(self, type):
        type = type.upper()
        if type == 'E':
            return self.is_e_ready
        elif type == 'Q':
            return self.is_q_ready
        elif type == 'A':
            return self.is_a_ready
        else:
            raise ValueError('Illegal type')


class Zero(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)


class Sakiri(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=20)


class Jiuyuan(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)


class Hathor(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)


class Fadia(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=20)


class Daffodill(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=20)


class Baicang(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=14, q_cd=20)


class Chiz(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=3, q_cd=15)


class Adler(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=20)


class Aurelia(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=15, q_cd=15)


class Edgar(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=20)


class Haniel(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=20, q_cd=20)


class Mint(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=6, q_cd=15)


class Skia(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=15, q_cd=15)


class Nanally(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)


class Hotori(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=0)

    def use_q(self):
        self.device.click(SKILL_Q)
        self.device.sleep((5.9, 6.1))
        t = Timer(8)
        while not t.reached:
            self.use_a()


class Lacrimosa(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=20)


CHINESE_TO_CHARA = {
    '零': Zero,
    '早雾': Sakiri,
    '九原': Jiuyuan,
    '哈索尔': Hathor,
    '法帝娅': Fadia,
    '达芙蒂尔': Daffodill,
    '白藏': Baicang,
    '小吱': Chiz,
    '阿德勒': Adler,
    '海月': Aurelia,
    '埃德嘉': Edgar,
    '哈尼娅': Haniel,
    '薄荷': Mint,
    '翳': Skia,
    '娜娜莉': Nanally,
    '浔': Hotori,
    '安魂曲': Lacrimosa
}