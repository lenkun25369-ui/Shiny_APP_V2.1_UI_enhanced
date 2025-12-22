from shiny import App, ui, render, reactive
import requests
import json

# =========================================================
# 🎨 Global CSS (Clinical Dashboard Style)
# =========================================================
GLOBAL_CSS = """
body {
  background-color: #f5f7fa;
}

.card {
  background: white;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.08);
  margin-bottom: 20px;
}

.risk-number {
  font-size: 52px;
  font-weight: 800;
  margin: 0;
}

.risk-low  { color: #2e7d32; }
.risk-mid  { color: #f9a825; }
.risk-high { color: #c62828; }

.risk-bar {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(
    to right,
    #c8e6c9,
    #fff59d,
    #ef9a9a
  );
  margin-top: 14px;
  position: relative;
}

.risk-marker {
  position: absolute;
  top: -4px;
  width: 2px;
  height: 20px;
  background: black;
}

.factor-row {
  display: flex;
  align-items: center;
  margin: 6px 0;
}

.factor-yes { color: #2e7d32; font-weight: 600; }
.factor-no  { color: #c62828; font-weight: 600; }

.factor-icon {
  width: 22px;
}
"""

# =========================================================
# 📊 CHARM risk table
# =========================================================
CHARM_TABLE = {
    0: 0.36,
    1: 1.89,
    2: 5.79,
    3: 12.97,
    4: 23.58,
    5: 34.15
}

# =========================================================
# 🧩 UI
# =========================================================
app_ui = ui.page_fluid(

    ui.tags.style(GLOBAL_CSS),

    # -------------------------------
    # 🔐 Read token / pid / fhir / obs from URL hash
    # -------------------------------
    ui.tags.script("""
    (function () {
      const params = new URLSearchParams(window.location.hash.substring(1));
      function send() {
        if (window.Shiny?.setInputValue) {
          ["token","pid","fhir","obs"].forEach(k =>
            Shiny.setInputValue(k, params.get(k))
          );
        } else {
          setTimeout(send, 300);
        }
      }
      send();
    })();
    """),

    ui.tags.style("#token,#pid,#fhir,#obs{display:none;}"),
    ui.input_text("token",""),
    ui.input_text("pid",""),
    ui.input_text("fhir",""),
    ui.input_text("obs",""),

    ui.h2("CHARM In-hospital Mortality Risk"),

    ui.layout_sidebar(

        # ================= Sidebar =================
        ui.sidebar(
            ui.p("Clinical variables (auto-populated from FHIR, editable)"),

            ui.input_radio_buttons("chills", "Chills",
                {"No":"No","Yes":"Yes"}, selected="No", inline=True),

            ui.input_radio_buttons("hypothermia", "Hypothermia (< 36°C)",
                {"No":"No","Yes":"Yes"}, selected="No", inline=True),

            ui.input_radio_buttons("anemia", "Anemia (RBC < 4M/µL)",
                {"No":"No","Yes":"Yes"}, selected="No", inline=True),

            ui.input_radio_buttons("rdw", "RDW > 14.5%",
                {"No":"No","Yes":"Yes"}, selected="No", inline=True),

            ui.input_radio_buttons("malignancy", "History of malignancy",
                {"No":"No","Yes":"Yes"}, selected="No", inline=True),
        ),

        # ================= Main =================
        ui.div(

            # -------- Risk summary card --------
            ui.div(
                {"class":"card"},
                ui.h4("Estimated Mortality Risk"),
                ui.output_ui("risk_number"),
                ui.output_ui("risk_label"),
                ui.output_ui("risk_bar"),
                ui.p("Lower than typical sepsis in-hospital mortality.",
                     style="color:#666; margin-top:10px;")
            ),

            # -------- Factors card --------
            ui.div(
                {"class":"card"},
                ui.h4("Contributing Clinical Factors"),
                ui.output_ui("factor_list")
            ),

            # -------- Reference --------
            ui.div(
                {"class":"card"},
                ui.p("CHARM score · FHIR-based · Reference available"),
                ui.a("Click here to see the reference",
                     href="https://www.ncbi.nlm.nih.gov/pubmed/?term=27832977"),
                ui.p("Developed by Dr. Chin-Chieh Wu",
                     style="color:#777; margin-top:6px;")
            )
        )
    )
)

# =========================================================
# 🧠 Server
# =========================================================
def server(input, output, session):

    # ---------- CHARM score ----------
    @reactive.Calc
    def charm_score():
        return sum([
            input.chills() == "Yes",
            input.hypothermia() == "Yes",
            input.anemia() == "Yes",
            input.rdw() == "Yes",
            input.malignancy() == "Yes",
        ])

    # ---------- Risk number ----------
    @output
    @render.ui
    def risk_number():
        prob = CHARM_TABLE[charm_score()]
        cls = "risk-low" if prob < 5 else "risk-mid" if prob < 20 else "risk-high"
        return ui.p(f"{prob:.2f} %", class_=f"risk-number {cls}")

    # ---------- Risk label ----------
    @output
    @render.ui
    def risk_label():
        prob = CHARM_TABLE[charm_score()]
        if prob < 5:
            txt, cls = "● Very Low Risk", "risk-low"
        elif prob < 20:
            txt, cls = "● Moderate Risk", "risk-mid"
        else:
            txt, cls = "● High Risk", "risk-high"
        return ui.p(txt, class_=cls)

    # ---------- Risk bar ----------
    @output
    @render.ui
    def risk_bar():
        prob = CHARM_TABLE[charm_score()]
        left = min(prob / 40 * 100, 100)
        return ui.div(
            {"class":"risk-bar"},
            ui.div({"class":"risk-marker",
                    "style":f"left:{left}%"}))

    # ---------- Factor list ----------
    @output
    @render.ui
    def factor_list():

        def row(label, val):
            yes = val == "Yes"
            return ui.div(
                {"class":"factor-row"},
                ui.span("✔" if yes else "✘",
                        class_="factor-icon " +
                               ("factor-yes" if yes else "factor-no")),
                ui.span(label)
            )

        return ui.div(
            row("Chills", input.chills()),
            row("Hypothermia (< 36°C)", input.hypothermia()),
            row("Anemia (RBC < 4M/µL)", input.anemia()),
            row("RDW > 14.5%", input.rdw()),
            row("History of malignancy", input.malignancy()),
        )

# =========================================================
# 🚀 App
# =========================================================
app = App(app_ui, server)
