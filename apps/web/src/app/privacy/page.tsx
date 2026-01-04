"use client";

import Link from "next/link";

export default function PrivacyPolicyPage() {
    return (
        <div className="min-h-screen bg-background">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid-lithium opacity-30 pointer-events-none" />
            <div className="fixed inset-0 gradient-radial-lithium pointer-events-none" />

            <div className="relative z-10 container mx-auto px-6 py-16 max-w-4xl">
                {/* Header */}
                <div className="mb-12">
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-8"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        Ana Sayfaya Dön
                    </Link>

                    <h1 className="text-4xl font-bold gradient-text-lithium mb-4">
                        Gizlilik Politikası
                    </h1>
                    <p className="text-muted-foreground">
                        Son güncelleme: 4 Ocak 2026
                    </p>
                </div>

                {/* Content */}
                <div className="glass-card rounded-2xl p-8 space-y-8">
                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">1. Giriş</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Lithium Bot olarak, gizliliğinize saygı duyuyor ve kişisel verilerinizin
                            korunmasına büyük önem veriyoruz. Bu politika, hangi verileri topladığımızı
                            ve nasıl kullandığımızı açıklamaktadır.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">2. Toplanan Veriler</h2>
                        <p className="text-muted-foreground leading-relaxed mb-4">
                            Hizmetlerimizi sağlamak için aşağıdaki verileri topluyoruz:
                        </p>
                        <ul className="text-muted-foreground space-y-2 list-disc list-inside">
                            <li>Discord Kullanıcı ID&apos;si ve kullanıcı adı</li>
                            <li>Sunucu ID&apos;si ve sunucu adı</li>
                            <li>Bot komutları ve ayarları</li>
                            <li>Moderasyon logları (uyarılar, yasaklar vb.)</li>
                            <li>Sunucu istatistikleri ve analitik verileri</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">3. Verilerin Kullanımı</h2>
                        <p className="text-muted-foreground leading-relaxed mb-4">
                            Topladığımız verileri şu amaçlarla kullanıyoruz:
                        </p>
                        <ul className="text-muted-foreground space-y-2 list-disc list-inside">
                            <li>Bot özelliklerini çalıştırmak ve geliştirmek</li>
                            <li>Sunucu ayarlarını ve tercihlerini saklamak</li>
                            <li>Moderasyon işlemlerini kayıt altına almak</li>
                            <li>Hizmet kalitesini artırmak için analiz yapmak</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">4. Veri Paylaşımı</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Verilerinizi üçüncü taraflarla paylaşmıyoruz. Verileriniz yalnızca hizmet
                            sağlayıcılarımız (sunucu altyapısı) tarafından güvenli bir şekilde saklanır.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">5. Veri Güvenliği</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Verilerinizi korumak için endüstri standardı güvenlik önlemleri kullanıyoruz.
                            Tüm veriler şifreli bağlantılar üzerinden iletilir ve güvenli sunucularda saklanır.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">6. Veri Saklama</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Verilerinizi, hizmetlerimizi aktif olarak kullandığınız sürece saklarız.
                            Bot sunucunuzdan kaldırıldığında, ilgili verileri makul bir süre içinde sileriz.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">7. Haklarınız</h2>
                        <p className="text-muted-foreground leading-relaxed mb-4">
                            Aşağıdaki haklara sahipsiniz:
                        </p>
                        <ul className="text-muted-foreground space-y-2 list-disc list-inside">
                            <li>Verilerinize erişim talep etme</li>
                            <li>Verilerinizin düzeltilmesini isteme</li>
                            <li>Verilerinizin silinmesini talep etme</li>
                            <li>Veri işlemeye itiraz etme</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">8. İletişim</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Gizlilik politikamızla ilgili sorularınız veya veri talepleriniz için
                            bizimle iletişime geçebilirsiniz.
                        </p>
                    </section>
                </div>

                {/* Footer */}
                <div className="mt-12 text-center">
                    <p className="text-muted-foreground text-sm">
                        © 2026 Lithium Bot. Tüm hakları saklıdır.
                    </p>
                </div>
            </div>
        </div>
    );
}
