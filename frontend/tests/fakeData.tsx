import { HttpResponse, http } from "msw";
import { getServerUrl } from "../src/api/getServerUrl";
import { AnalysisRequestParams } from "../src/types/Analysis";
import { Override } from "../src/types/Override";

// const fakeExperiments: Experiment[] = [
//   {
//     id: "ID-ALL",
//     props: {
//       unconverted_mtime: 100,
//       converted_mtime: 200,
//       processed_mtime: 300,
//       overridden: false
//     }
//   },
//   {
//     id: "ID-UNC-CON",
//     props: {
//       unconverted_mtime: 100,
//       converted_mtime: 200,
//       processed_mtime: -1,
//       overridden: false
//     }
//   },
//   {
//     id: "ID-ERR",
//     props: {
//       unconverted_mtime: 100,
//       converted_mtime: "Error",
//       processed_mtime: -1,
//       overridden: false
//     }
//   },
//   {
//     id: "ID-UNC-ONLY",
//     props: {
//       unconverted_mtime: 100,
//       converted_mtime: -1,
//       processed_mtime: -1,
//       overridden: false
//     }
//   },
//   {
//     id: "ID-NONE",
//     props: {
//       unconverted_mtime: -1,
//       converted_mtime: -1,
//       processed_mtime: -1,
//       overridden: false
//     }
//   }
// ];

const fakeOverrides: Override[] = [
  {
    pattern: "ID-OVR",
    analysis_step_overrides: [{ mtime: 0 }, { mtime: 0 }],
  },
  {
    pattern: "ID-OVR-2",
    analysis_step_overrides: [{ mtime: 100 }, { mtime: 200 }],
  },
];

const serverUrl = getServerUrl();

export const selectiveAnalysisHandler = (
  desiredParams: AnalysisRequestParams
) => {
  return http.post(`${serverUrl}/analyses`, async ({ request }) => {
    const body = (await request.json()) as AnalysisRequestParams;
    if (
      body.steps_to_analyze.every((v, i) => v == desiredParams.steps_to_analyze[i]) &&
      body.pattern === desiredParams.pattern
    ) {
      return HttpResponse.json({ current: null, queued: [] });
    } else {
      return HttpResponse.text("Invalid", { status: 400 });
    }
  });
};

export const overrideHandlers = [
  http.get(`${serverUrl}/overrides`, () => {
    return HttpResponse.json(fakeOverrides);
  }),
  http.post(`${serverUrl}/overrides`, async ({ request }) => {
    const body = (await request.json()) as Override;
    return HttpResponse.json(fakeOverrides.concat(body));
  }),
  http.delete(`${serverUrl}/overrides/:id`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json(fakeOverrides.filter((ovr) => ovr.pattern !== id));
  }),
];

export const analysisStepsHandler = http.get(`${serverUrl}/analysis_steps`, async () => {
  return HttpResponse.json(["Unconverted Data", "Converted Data"]);
});
