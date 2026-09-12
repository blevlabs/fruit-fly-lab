class NoisyConnorStevens(Model):
    Time_Scale = 1e3 # s to ms
    Default_States = dict(
        spike=0., v1=-60., v2=-60.,
        v=(-60, -80, 80),
        n=(0., 0., 1.), m=(0., 0., 1.), h=(1., 0., 1.),
        a=(1., 0., 1.), b=(1., 0., 1.),
        refactory=0.)
    Default_Params = dict(ms=-5.3, ns=-4.3, hs=-12., \
        gNa=120., gK=20., gL=0.3, ga=47.7, \
        ENa=55., EK=-72., EL=-17., Ea=-75., \
        sigma=2.05, refperiod=1.)

    def ode(self, stimulus=0.):

        alpha = np.exp(-(self.v+50.+self.ns)/10.)-1.
        if abs(alpha) <= 1e-7:
            alpha = 0.1
        else:
            alpha = -0.01*(self.v+50.+self.ns)/alpha
        beta = .125*np.exp(-(self.v+60.+self.ns)/80.)
        n_inf = alpha/(alpha+beta)
        tau_n = 2./(3.8*(alpha+beta))

        alpha = np.exp(-(self.v+35.+self.ms)/10.)-1.
        if abs(alpha) <= 1e-7:
            alpha = 1.
        else:
            alpha = -.1*(self.v+35.+self.ms)/alpha
        beta = 4.*np.exp(-(self.v+60.+self.ms)/18.)
        m_inf = alpha/(alpha+beta)
        tau_m = 1./(3.8*(alpha+beta))

        alpha = .07*np.exp(-(self.v+60.+self.hs)/20.)
        beta = 1./(1.+np.exp(-(self.v+30.+self.hs)/10.))
        h_inf = alpha/(alpha+beta)
        tau_h = 1./(3.8*(alpha+beta))

        a_inf = np.cbrt(.0761*np.exp((self.v+94.22)/31.84)/(1.+np.exp((self.v+1.17)/28.93)))
        tau_a = .3632+1.158/(1.+np.exp((self.v+55.96)/20.12))
        b_inf = np.power(1/(1+np.exp((self.v+53.3)/14.54)), 4.)
        tau_b = 1.24+2.678/(1+np.exp((self.v+50)/16.027))

        i_na = self.gNa * np.power(self.m, 3) * self.h * (self.v - self.ENa)
        i_k = self.gK * np.power(self.n, 4) * (self.v - self.EK)
        i_l = self.gL * (self.v - self.EL)
        i_a = self.ga * np.power(self.a, 3) * self.b * (self.v - self.Ea)

        self.d_v = stimulus - i_na - i_k - i_l - i_a
        self.d_n = (n_inf-self.n)/tau_n + random.gauss(0., self.sigma)
        self.d_m = (m_inf-self.m)/tau_m + random.gauss(0., self.sigma)
        self.d_h = (h_inf-self.h)/tau_h + random.gauss(0., self.sigma)
        self.d_a = (a_inf-self.a)/tau_a + random.gauss(0., self.sigma)
        self.d_b = (b_inf-self.b)/tau_b + random.gauss(0., self.sigma)

        self.d_refactory = (self.refactory < 0)

    def post(self):
        self.spike = (self.v1 <= self.v2) * (self.v <= self.v2) * (self.v2 > -30.)
        self.v1 = self.v2
        self.v2 = self.v
        self.spike = (self.spike > 0.) * (self.refactory >= 0)
        self.refactory -= (self.spike > 0.) * self.refperiod

