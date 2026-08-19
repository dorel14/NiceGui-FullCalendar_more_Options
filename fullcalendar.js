import { loadResource } from "../../static/utils/resources.js";
let pendingInfo = null;  // Stocke l'info + successCallback entre-temps

export default {
  template: "<div></div>",
  props: {
    options: Object,
    resource_path: String,
  },
  async mounted() {
    await this.$nextTick(); // NOTE: wait for window.path_prefix to be set
    await loadResource('https://cdn.jsdelivr.net/npm/ical.js/build/ical.min.js');
    await loadResource('https://cdn.jsdelivr.net/npm/rrule@2.6.4/dist/es5/rrule.min.js');
    await loadResource(window.path_prefix + `${this.resource_path}/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/locales-all.global.min.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/multimonth/index.global.min.js`); 
    await loadResource(window.path_prefix + `${this.resource_path}/icalendar.index.global.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/rrule.index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/daygrid/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/timegrid/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/list/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resource_path}/interaction/index.global.min.js`);

    this.options.eventClick = (info) => this.$emit("click", { info });
    this.options.dateClick = (info) => this.$emit("click", { info });

    // Initialize calendar before using it
    this.calendar = new FullCalendar.Calendar(this.$el, this.options);

    // --- New : events as function (JS → Python → JS) ---
    // FullCalendar calls this function when it needs data.
    // info is saved + successCallback, and notify Python.
    this.options.events = (info, successCallback, failureCallback) => {
      pendingInfo = { info, successCallback, failureCallback };
      this.$emit("fetch_events", {
        startStr: info.startStr,
        endStr: info.endStr,
        timeZone: info.timeZone,
      });
    };

    console.log("Calendar:", this.calendar);
    console.log("Calendar options:", this.options);
    console.log("Events source:", this.options.events);

    this.calendar.render();
  },
  methods: {
    update_calendar() {
      if (this.calendar) {        
        this.calendar.setOption("events", this.options.events);
        console.log("Calendar options:", this.options);
        console.log(this.options.events);
        this.calendar.refetchEvents()
        this.calendar.render();
      }
    },
    // ← Method called by Python via Element.run_method()
    provide_events(events) {
      if (pendingInfo) {
        // FullCalendar v5/v6 : successCallback can be direct or inside fetchInfo
        const cb = pendingInfo.successCallback || pendingInfo.info.successCallback;
        if (cb) {
          cb(events);
        } else {
          // Fallback : refresh EventSource directly
          const source = this.calendar.getEventSourceById?.('dynamic');
          if (source) source.addEventSource({ events, id: 'dynamic' });
        }
        pendingInfo = null;
      }
      this.calendar.refetchEvents();
    },
  },
};
