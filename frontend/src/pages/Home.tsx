import {
  Flex,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
} from "@chakra-ui/react";
import NavBar from "../layout/NavBar";
import Inventory from "../components/inventory/Inventory";

const Home = () => {
  return (
    <Flex flexDirection="column" gap={10} padding={6} w="100%">
      <NavBar />
      <Tabs w="100%" isLazy>
        <TabList w="fit-content">
          <Tab>All</Tab>
          <Tab>To be analyzed</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <Inventory />
          </TabPanel>
          <TabPanel>
            <Inventory filter="to_be_analyzed" />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Flex>
  );
};

export default Home;
