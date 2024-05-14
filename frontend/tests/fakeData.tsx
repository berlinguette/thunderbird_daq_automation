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

export const analysisHandler = http.post(`${serverUrl}/analyses`, async ({ request }) => {
  const body = await request.json() as AnalysisParams;
  const filteredExperiments = fakeExperiments.filter((exp) => {
    if (body.convert_unconverted && exp.props.unconverted_mtime !== -1) {
      return true;
    }
    if (body.process_converted && exp.props.converted_mtime !== -1) {
      return true;
    }
    return false;
  });
  return HttpResponse.json({
    current: filteredExperiments[0],
    queued: filteredExperiments.slice(1)
  });
});