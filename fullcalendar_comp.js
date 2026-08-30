import { loadResource } from "../../static/utils/resources.js";
let pendingInfo = null;  // Stocke l'info + successCallback entre-temps

export default {
  template: "<div></div>",
  props: {
    options: Object,
    resourcePath: String,
  },
  async mounted() {
    await this.$nextTick(); // NOTE: wait for window.path_prefix to be set
    await loadResource('https://cdn.jsdelivr.net/npm/ical.js/build/ical.min.js');
    await loadResource('https://cdn.jsdelivr.net/npm/rrule@2.6.4/dist/es5/rrule.min.js');
    await loadResource(window.path_prefix + `${this.resourcePath}/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/locales-all.global.min.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/multimonth/index.global.min.js`); 
    await loadResource(window.path_prefix + `${this.resourcePath}/icalendar.index.global.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/rrule.index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/daygrid/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/timegrid/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/list/index.global.min.js`);
    await loadResource(window.path_prefix + `${this.resourcePath}/interaction/index.global.min.js`);

    // CONFIRM which file the browser actually loaded.
    console.log('[FullCalendar] component v4 loaded');

    // Deep-clone that guarantees JSON-serializability (strips circular refs and
    // DOM events like PointerEvent). This makes the emit impossible to break.
    const safeClone = (value, seen = new WeakSet()) => {
      if (value === null || value === undefined) return value;
      const t = typeof value;
      if (t === 'string' || t === 'number' || t === 'boolean') return value;
      if (value instanceof Date) return value.toISOString();
      if (t !== 'object') return String(value);
      if (seen.has(value)) return '[Circular]';
      seen.add(value);
      const out = Array.isArray(value)
        ? value.map((v) => safeClone(v, seen))
        : Object.fromEntries(Object.keys(value).map((k) => [k, safeClone(value[k], seen)]));
      seen.delete(value);
      return out;
    };

    // FullCalendar's info objects contain a `jsEvent` (PointerEvent) with circular
    // references, so we must emit only serializable fields, not the whole `info`.
    const serializeEvent = (e) => e ? {
      id: e.id,
      title: e.title,
      start: e.startStr,
      end: e.endStr,
      allDay: e.allDay,
      color: e.backgroundColor,
    } : null;
    let selectedDate = null;
    this.options.eventClick = (info) => this.$emit("click", safeClone({
      info: { event: serializeEvent(info.event), date: info.dateStr },
    }));
    this.options.dateClick = (info) => {
      selectedDate = info.date;
      this.$emit("click", safeClone({ info: { date: info.dateStr } }));
    };
    // Custom "jour" button: shows the day that was last clicked, not today.
    this.options.customButtons = {
      daySelected: {
        text: 'jour',
        click: () => this.calendar.changeView('timeGridDay', selectedDate || new Date()),
      },
    };

    // --- events as function (JS -> Python -> JS) ---
    // FullCalendar calls this function when it needs data.
    // We build a fully serializable payload (FullCalendar's `info` may contain
    // circular references, which would break NiceGUI's JSON.stringify).
    this.options.events = (info, successCallback, failureCallback) => {
      pendingInfo = { info, successCallback, failureCallback };
      const payload = {
        startStr: info.start instanceof Date ? info.start.toISOString() : String(info.startStr ?? ''),
        endStr: info.end instanceof Date ? info.end.toISOString() : String(info.endStr ?? ''),
        timeZone: String(info.timeZone ?? ''),
      };
      this.$emit("fetch_events", safeClone(payload));
    };

    this.calendar = new FullCalendar.Calendar(this.$el, this.options);
    this.calendar.render();
  },
  methods: {
    update_calendar() {
      if (this.calendar) {
        this.calendar.setOption("events", this.options.events);
        this.calendar.refetchEvents();
        this.calendar.render();
      }
    },
    // <- Method called by Python via Element.run_method()
    provide_events(events) {
      if (pendingInfo) {
        const cb = pendingInfo.successCallback || (pendingInfo.info && pendingInfo.info.successCallback);
        if (cb) {
          cb(events);
        } else {
          // Fallback : refresh EventSource directly
          const source = this.calendar.getEventSourceById?.('dynamic');
          if (source) source.addEventSource({ events, id: 'dynamic' });
          else this.calendar.addEventSource({ events, id: 'dynamic' });
        }
        pendingInfo = null;
      }
      // NOTE: do NOT call refetchEvents() here. successCallback already feeds the
      // events to FullCalendar; an extra refetch would re-invoke the events function
      // and create an infinite fetch loop.
    },
  },
};
