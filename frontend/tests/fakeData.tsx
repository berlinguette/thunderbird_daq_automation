import { HttpResponse, http } from "msw";
import { getServerUrl } from "../src/api/getServerUrl";
import { AnalysisParams } from "../src/types/Analysis";
import { Experiment } from "../src/types/Experiment";

const fakeExperiments: Experiment[] = [
  {
    id: "ID-ALL",
    props: {
      unconverted_mtime: 100,
      converted_mtime: 200,
      processed_mtime: 300,
      overridden: false
    }
  },
  {
    id: "ID-UNC-CON",
    props: {
      unconverted_mtime: 100,
      converted_mtime: 200,
      processed_mtime: -1,
      overridden: false
    }
  },
  {
    id: "ID-ERR",
    props: {
      unconverted_mtime: 100,
      converted_mtime: "Error",
      processed_mtime: -1,
      overridden: false
    }
  },
  {
    id: "ID-UNC-ONLY",
    props: {
      unconverted_mtime: 100,
      converted_mtime: -1,
      processed_mtime: -1,
      overridden: false
    }
  },
  {
    id: "ID-NONE",
    props: {
      unconverted_mtime: -1,
      converted_mtime: -1,
      processed_mtime: -1,
      overridden: false
    }
  }
];

const serverUrl = getServerUrl();

export const selectiveAnalysisHandler = (desiredParams: AnalysisParams) => {
  return http.post(`${serverUrl}/analyses`, async ({ request }) => {
    const body = await request.json() as AnalysisParams;
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