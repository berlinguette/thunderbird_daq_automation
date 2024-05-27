import { HttpResponse, http } from "msw";
import { getServerUrl } from "../src/api/getServerUrl";
import { AnalysisRequestParams } from "../src/types/Analysis";
import { Experiment } from "../src/types/Experiment";

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

const fakeOverrides: Experiment[] = [
  {
    id: "ID-OVR",
    props: {
      unconverted_mtime: 0,
      converted_mtime: 0,
      processed_mtime: 0,
      overridden: true
    }
  }
];

const serverUrl = getServerUrl();

export const selectiveAnalysisHandler = (desiredParams: AnalysisRequestParams) => {
  return http.post(`${serverUrl}/analyses`, async ({ request }) => {
    const body = await request.json() as AnalysisRequestParams;
    if (
      body.convert_unconverted === desiredParams.convert_unconverted &&
      body.process_converted === desiredParams.process_converted &&
      body.pattern === desiredParams.pattern &&
      body.force === desiredParams.force
    ) {
      return HttpResponse.json({});
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
    const body = await request.json() as Experiment;
    return HttpResponse.json(fakeOverrides.concat(body));
  }),
  http.delete(`${serverUrl}/overrides/:id`, ({ params }) => {
    const { id } = params;
    return HttpResponse.json(fakeOverrides.filter((ovr) => ovr.id !== id));
  })
];