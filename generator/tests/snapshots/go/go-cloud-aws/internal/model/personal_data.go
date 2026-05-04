package model

import "fmt"

type PersonalData struct {
	ID        string  `avro:"id"`
	Name      string  `avro:"name"`
	Birthday  string  `avro:"birthday"`
	Timestamp *string `avro:"timestamp"`
}

func (p PersonalData) String() string {
	ts := "<nil>"
	if p.Timestamp != nil {
		ts = *p.Timestamp
	}
	return fmt.Sprintf(
		"--- Personal Data ---\n"+
			"  ID:        %s\n"+
			"  Name:      %s\n"+
			"  Birthday:  %s\n"+
			"  Timestamp: %s\n"+
			"---------------------",
		p.ID, p.Name, p.Birthday, ts,
	)
}
