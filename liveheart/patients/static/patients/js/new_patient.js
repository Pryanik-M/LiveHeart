document.addEventListener("DOMContentLoaded", () => {

    /* ================= helpers ================= */

    const getVal = (selector) => {
        const el = document.querySelector(selector);
        if (!el) return null;
        const v = parseFloat(el.value.replace(",", "."));
        return isNaN(v) ? null : v;
    };

    const setVal = (selector, value, digits = 2) => {
        const el = document.querySelector(selector);
        if (!el) return;
        el.value = (value === null || isNaN(value)) ? "" : value.toFixed(digits);
    };

    /* ================= BMI / BSA ================= */

    function calcBSA() {
        const h = getVal("#height");
        const w = getVal("#weight");
        if (!h || !w) {
            setVal("#bsa", null);
            return null;
        }
        const bsa = Math.sqrt((h * w) / 3600);
        setVal("#bsa", bsa, 2);
        return bsa;
    }

    function calcBMI() {
        const h = getVal("#height");
        const w = getVal("#weight");
        if (!h || !w) {
            setVal("#bmi", null);
            return;
        }
        setVal("#bmi", w / Math.pow(h / 100, 2), 1);
    }

    /* ================= LEFT VENTRICLE ================= */

    function calcLV(bsa) {
        const edv = getVal('[data-lv="edv"]');
        const esv = getVal('[data-lv="esv"]');
        const edd = getVal('[data-lv="edd"]');
        const esd = getVal('[data-lv="esd"]');
        const ivsd = getVal('[data-lv="ivsd"]');
        const pw = getVal('[data-lv="pw"]');
        const hr = getVal('[data-lv="hr"]');

        // ФС
        if (edd && esd) {
            setVal('[data-lv-calc="fs"]', ((edd - esd) / edd) * 100, 1);
        } else setVal('[data-lv-calc="fs"]', null);

        // УО + ФВ
        let sv = null;
        if (edv && esv) {
            sv = edv - esv;
            setVal('[data-lv-calc="sv"]', sv, 1);
            setVal('[data-lv-calc="ef"]', (sv / edv) * 100, 1);
        } else {
            setVal('[data-lv-calc="sv"]', null);
            setVal('[data-lv-calc="ef"]', null);
        }

        // МО / СВ / СИ
        if (sv && hr) {
            setVal('[data-lv-calc="mo"]', sv * hr, 0);
            setVal('[data-lv-calc="co"]', (sv * hr) / 1000, 2);
            if (bsa) setVal('[data-lv-calc="ci"]', ((sv * hr) / 1000) / bsa, 2);
            else setVal('[data-lv-calc="ci"]', null);
        } else {
            setVal('[data-lv-calc="mo"]', null);
            setVal('[data-lv-calc="co"]', null);
            setVal('[data-lv-calc="ci"]', null);
        }

        // ММЛЖ + ИММЛЖ (Devereux)
        if (edd && ivsd && pw) {
            const lvm = 0.8 * (1.04 * Math.pow(edd + ivsd + pw, 3) - Math.pow(edd, 3)) + 0.6;
            setVal('[data-lv-calc="lvm"]', lvm, 0);
            if (bsa) setVal('[data-lv-calc="lvmi"]', lvm / bsa, 1);
            else setVal('[data-lv-calc="lvmi"]', null);
        } else {
            setVal('[data-lv-calc="lvm"]', null);
            setVal('[data-lv-calc="lvmi"]', null);
        }

        // ОТС
        if (pw && edd) {
            setVal('[data-lv-calc="rwt"]', (2 * pw) / edd, 2);
        } else setVal('[data-lv-calc="rwt"]', null);
    }

    /* ================= OTHER CHAMBERS ================= */

    function calcLA(bsa) {
        const lav = getVal('[data-oc="lav"]');
        if (lav && bsa) setVal('[data-oc-calc="lavi"]', lav / bsa, 1);
        else setVal('[data-oc-calc="lavi"]', null);
    }

    /* ================= MITRAL / TRICUSPID ================= */

    function calcEA(group) {
        const e = getVal(`[data-${group}="e"]`);
        const a = getVal(`[data-${group}="a"]`);
        if (e && a) setVal(`[data-${group}-calc="ea"]`, e / a, 2);
        else setVal(`[data-${group}-calc="ea"]`, null);
    }

    /* ================= PULMONARY ARTERY ================= */

    const mpapTable = [
        { r: 0.20, v: 69 },
        { r: 0.25, v: 50 },
        { r: 0.30, v: 36 },
        { r: 0.35, v: 26 },
        { r: 0.40, v: 19 },
        { r: 0.45, v: 13 }
    ];

    function calcPA() {
        const at = getVal('[data-pa="at"]');
        const et = getVal('[data-pa="et"]');

        if (at && et) {
            const ratio = at / et;
            setVal('[data-pa-calc="ratio"]', ratio, 2);

            const closest = mpapTable.reduce((a, b) =>
                Math.abs(b.r - ratio) < Math.abs(a.r - ratio) ? b : a
            );

            setVal('[data-pa-calc="mpap"]', closest.v, 0);
        } else {
            setVal('[data-pa-calc="ratio"]', null);
            setVal('[data-pa-calc="mpap"]', null);
        }
    }

    /* ================= MAIN ================= */

    function recalcAll() {
        calcBMI();
        const bsa = calcBSA();
        calcLV(bsa);
        calcLA(bsa);
        calcEA("mv");
        calcEA("tv");
        calcPA();
    }

    document.querySelectorAll("input").forEach(el =>
        el.addEventListener("input", recalcAll)
    );

    recalcAll();
});

async function submitForm() {
    const payload = {
        patient: {
            full_name: document.getElementById("full_name").value,
            age: +document.getElementById("age").value,
            exam_datetime: document.getElementById("exam_datetime").value,
            height: +document.getElementById("height").value || null,
            weight: +document.getElementById("weight").value || null,
            bmi: +document.getElementById("bmi").value || null,
            bsa: +document.getElementById("bsa").value || null,
        },
        echo: collectEchoData() // мы её уже почти сделали
    };

    const res = await fetch("", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.status === "ok") {
        alert("Пациент сохранён");
        window.location.href = "/auth/dashboard/";
    }
}
