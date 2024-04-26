import { Box, Flex } from "@chakra-ui/react"
import { Link, useLocation } from "react-router-dom"

const NavBar = () => {
  const location = useLocation();

  const nav = [
    {
      "name": "Dashboard",
      "href": "/"
    },
    {
      "name": "Queue",
      "href": "/#"
    }
  ];

  return (
    <Flex gap={8}>
      <Box fontSize="xx-large" fontWeight={600} marginY="auto">Thunderbird Data Analyzer</Box>
      <Flex alignItems="center" fontSize="medium" fontWeight={400} gap={4}>
        {nav.map((link) => (
          <Link to={link.href} key={link.href}>
            <Box
              paddingY={4}
              paddingX={5}
              bg={location.pathname === link.href ? "blue.600" : "transparent"}
              color={location.pathname === link.href ? "white" : " black"}
              fontWeight={location.pathname === link.href ? "600" : "400"}
              borderRadius={40}
            >
              {link.name}
            </Box>
          </Link>
        ))}
      </Flex>
    </Flex>
  );
};

export default NavBar